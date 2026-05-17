from __future__ import annotations

import os
import sys
import logging
import argparse
import statistics

from dataclasses import dataclass
from typing import Callable

import torch
import matplotlib.pyplot as plt

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

from src.game.game import Game
from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.game.score_rating import SCORE_CATEGORIES
from src.actions.action_handler import ActionHandler
from src.game.logging_observer import LoggingObserver
from src.input_handler import AutomaticInputHandler, InputHandler, RLInputHandler
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler
from src.input_handler.heuristics.fox_balancing import FoxBalancingInputHandler
from src.input_handler.heuristics.greedy_immediate import GreedyImmediateInputHandler
from src.input_handler.heuristics.resource_aware import ResourceAwareInputHandler

from model.policy_network import PolicyNetwork
from scripts.train_rl import require_phase3_metadata

logger = logging.getLogger(__name__)

HandlerFactory = Callable[[Board], InputHandler]


@dataclass
class BaselineResult:
    name: str
    scores: list[int]

    @property
    def mean(self) -> float:
        return statistics.mean(self.scores)

    @property
    def std(self) -> float:
        return statistics.stdev(self.scores) if len(self.scores) > 1 else 0.0

    @property
    def median(self) -> float:
        return statistics.median(self.scores)


def main() -> None:
    args = _parse_arguments()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    results = _run_all_baselines(args)
    _print_comparison_table(results)
    _print_category_table(results)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    _plot_overlaid_distributions(results, output_dir)
    _plot_learning_curve(args.log_dir, output_dir)

    logger.info("Evaluation complete. Plots saved to %s/", output_dir)

    if args.ci:
        _ci_gate(results)


_BASELINES: list[tuple[str, "HandlerFactory"]] = [
    ("Random", lambda _board: AutomaticInputHandler()),
    ("Always-Accept", lambda _board: AlwaysAcceptInputHandler()),
    ("Greedy", GreedyImmediateInputHandler),
    ("Fox-Balancing", FoxBalancingInputHandler),
    ("Resource-Aware", ResourceAwareInputHandler),
]


def _run_all_baselines(args: argparse.Namespace) -> list[BaselineResult]:
    results: list[BaselineResult] = []

    for name, factory in _BASELINES:
        logger.info("Running %s baseline (%d games)...", name, args.num_games)
        results.append(_run_baseline(name, factory, args.num_games))

    checkpoint = _resolve_checkpoint(args.checkpoint)
    if checkpoint is not None:
        logger.info("Running RL agent (%d games) from %s...", args.num_games, checkpoint)
        results.append(_run_rl_agent(checkpoint, args.num_games))
    else:
        logger.warning("No checkpoint found — skipping RL agent evaluation.")

    return results


def _run_baseline(name: str, factory: "HandlerFactory", num_games: int) -> BaselineResult:
    scores = [_play_standard_game(factory) for _ in range(num_games)]
    return BaselineResult(name=name, scores=scores)


def _play_standard_game(factory: "HandlerFactory") -> int:
    board = Board()
    game = Game(
        input_handler=factory(board),
        board=board,
        observer=LoggingObserver(),
        action_handler=ActionHandler(board=board),
    )
    return game.play()


def _run_rl_agent(checkpoint_path: str, num_games: int) -> BaselineResult:
    policy, augmented = _load_policy(checkpoint_path)
    policy_fn = _create_policy_fn(policy)
    scores = [_play_rl_game(policy_fn, augmented) for _ in range(num_games)]
    return BaselineResult(name="RL Agent", scores=scores)


def _play_rl_game(policy_fn, augmented: bool) -> int:
    board = Board()
    observer = RLObserver(board, augmented=augmented)
    handler = RLInputHandler(observer, policy_fn, training=False)
    game = Game(
        input_handler=handler,
        board=board,
        observer=observer,
        action_handler=ActionHandler(board=board),
    )
    return game.play()


def _load_policy(checkpoint_path: str) -> tuple[PolicyNetwork, bool]:
    checkpoint = torch.load(checkpoint_path, weights_only=True)
    require_phase3_metadata(checkpoint, checkpoint_path)
    policy = PolicyNetwork(
        state_size=checkpoint["state_size"],
        hidden1=checkpoint.get("hidden1", 256),
        hidden2=checkpoint.get("hidden2", 128),
    )
    policy.load_state_dict(checkpoint["policy_state_dict"])
    policy.eval()
    return policy, checkpoint["augmented"]


def _create_policy_fn(policy: PolicyNetwork):
    @torch.no_grad()
    def policy_fn(state: list[float], action_mask: list[bool]) -> tuple[int, float, float]:
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        mask_t = torch.tensor([float(m) for m in action_mask], dtype=torch.float32).unsqueeze(0)
        logits, value = policy(state_t)
        masked_logits = logits + (1.0 - mask_t) * (-1e8)
        action = masked_logits.argmax(dim=-1)
        dist = torch.distributions.Categorical(logits=masked_logits)
        log_prob = dist.log_prob(action)
        return action.item(), log_prob.item(), value.item()

    return policy_fn


def _print_comparison_table(results: list[BaselineResult]) -> None:
    header = f"{'Agent':<20} {'Mean':>8} {'Std':>8} {'Median':>8} {'Min':>6} {'Max':>6} {'N':>6}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r.name:<20} {r.mean:>8.1f} {r.std:>8.1f} {r.median:>8.1f} "
            f"{min(r.scores):>6} {max(r.scores):>6} {len(r.scores):>6}"
        )
    print("=" * len(header))
    _print_relative_improvements(results)


def _print_relative_improvements(results: list[BaselineResult]) -> None:
    if len(results) < 2:
        return
    base = results[0]
    print(f"\nRelative to {base.name}:")
    for r in results[1:]:
        improvement = (r.mean - base.mean) / base.mean * 100 if base.mean else 0.0
        print(f"  {r.name}: {improvement:+.1f}% mean score improvement")


def _category_label(lower: int, upper: int | None) -> str:
    if lower == 0:
        return f"Under {upper}"
    if upper is None:
        return f"{lower} and up"
    return f"{lower}–{upper - 1}"


_CATEGORY_LABELS: list[str] = [
    _category_label(lower, upper) for lower, upper, _ in SCORE_CATEGORIES
]


def _category_distribution(scores: list[int]) -> list[float]:
    if not scores:
        return [0.0] * len(SCORE_CATEGORIES)
    counts = [0] * len(SCORE_CATEGORIES)
    for score in scores:
        counts[_category_index(score)] += 1
    return [c / len(scores) * 100.0 for c in counts]


def _category_index(score: int) -> int:
    for i, (lower, upper, _) in enumerate(SCORE_CATEGORIES):
        if upper is None:
            if score >= lower:
                return i
        elif lower <= score < upper:
            return i
    return len(SCORE_CATEGORIES) - 1


def _print_category_table(results: list[BaselineResult]) -> None:
    name_width = max(len("Agent"), *(len(r.name) for r in results))
    cell_width = max(7, max(len(label) for label in _CATEGORY_LABELS) + 1)
    header = _format_category_header(name_width, cell_width)
    print("\n" + "=" * len(header))
    print("Score-category distribution (% of games)")
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for r in results:
        print(_format_category_row(r, name_width, cell_width))
    print("=" * len(header))


def _format_category_header(name_width: int, cell_width: int) -> str:
    return f"{'Agent':<{name_width}} " + " ".join(
        f"{label:>{cell_width}}" for label in _CATEGORY_LABELS
    )


def _format_category_row(result: BaselineResult, name_width: int, cell_width: int) -> str:
    dist = _category_distribution(result.scores)
    cells = " ".join(f"{pct:>{cell_width}.1f}" for pct in dist)
    return f"{result.name:<{name_width}} {cells}"


_CATEGORY_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]


def _plot_overlaid_distributions(results: list[BaselineResult], output_dir: str) -> None:
    grouped = _group_results_for_overlay(results)
    fig, ax = plt.subplots(figsize=(10, 6))
    legend_handles = []
    for i, result in enumerate(grouped):
        color = _CATEGORY_PALETTE[i % len(_CATEGORY_PALETTE)]
        ax.hist(
            result.scores, bins=30, density=True, alpha=0.45,
            color=color, edgecolor="black", linewidth=0.5,
        )
        legend_handles.append(
            plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor="black", linewidth=0.5,
                          label=f"{result.name} (μ={result.mean:.1f})")
        )
    _add_category_lines(ax)
    ax.set_xlim(0, 350)
    ax.set_xlabel("Score")
    ax.set_ylabel("Density")
    ax.set_title("Score Distributions — Random vs Heuristics vs RL")
    ax.legend(handles=legend_handles)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "score_distributions_overlay.png"), dpi=150)
    plt.close(fig)


_HEURISTIC_NAMES = {"Always-Accept", "Greedy", "Fox-Balancing", "Resource-Aware"}


def _group_results_for_overlay(results: list[BaselineResult]) -> list[BaselineResult]:
    random_result = _find_result(results, "Random")
    rl_result = _find_result(results, "RL Agent")
    heuristic_scores: list[int] = []
    for r in results:
        if r.name in _HEURISTIC_NAMES:
            heuristic_scores.extend(r.scores)

    grouped: list[BaselineResult] = []
    if random_result is not None:
        grouped.append(random_result)
    if heuristic_scores:
        grouped.append(BaselineResult(name="Heuristics (combined)", scores=heuristic_scores))
    if rl_result is not None:
        grouped.append(rl_result)
    return grouped


def _add_category_lines(ax) -> None:
    boundaries = sorted({lower for lower, _, _ in SCORE_CATEGORIES if lower > 0})
    for boundary in boundaries:
        ax.axvline(x=boundary, color="red", linestyle="--", alpha=0.4, linewidth=0.8)


def _plot_learning_curve(log_dir: str, output_dir: str) -> None:
    scores = _read_tensorboard_scores(log_dir)
    if not scores:
        logger.warning("No TensorBoard score data found in %s — skipping learning curve.", log_dir)
        return

    steps, values = zip(*scores)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(steps, values, alpha=0.3, color="blue", linewidth=0.5, label="Raw")
    smoothed = _smooth(values, window=50)
    ax.plot(steps[len(steps) - len(smoothed):], smoothed, color="blue", linewidth=2, label="Smoothed (w=50)")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Mean Score")
    ax.set_title("RL Agent Learning Curve")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "learning_curve.png"), dpi=150)
    plt.close(fig)


def _read_tensorboard_scores(log_dir: str) -> list[tuple[int, float]]:
    if EventAccumulator is None:
        logger.warning("tensorboard not installed — cannot read learning curve data.")
        return []

    if not os.path.isdir(log_dir):
        return []

    event_files = sorted(
        (
            os.path.join(log_dir, name)
            for name in os.listdir(log_dir)
            if name.startswith("events.out.tfevents")
        ),
        key=os.path.getmtime,
    )
    files_with_events = [(f, _load_score_events(f)) for f in event_files]
    files_with_events = [(f, ev) for f, ev in files_with_events if ev]
    if not files_with_events:
        return []

    chain = _build_resume_chain(files_with_events)
    return _concatenate_resume_chain(chain)


def _load_score_events(path: str) -> list[tuple[int, float]]:
    ea = EventAccumulator(path)
    ea.Reload()
    tag = "score/mean"
    if tag not in ea.Tags().get("scalars", []):
        return []
    return [(e.step, e.value) for e in ea.Scalars(tag)]


def _build_resume_chain(
    files_with_events: list[tuple[str, list[tuple[int, float]]]],
) -> list[list[tuple[int, float]]]:
    latest_events = files_with_events[-1][1]
    chain = [latest_events]
    if _is_fresh_start(latest_events):
        return chain
    current_first_step = latest_events[0][0]
    for _, events in reversed(files_with_events[:-1]):
        first_step, last_step = events[0][0], events[-1][0]
        if first_step < current_first_step <= last_step:
            chain.insert(0, events)
            current_first_step = first_step
            if _is_fresh_start(events):
                break
    return chain


def _is_fresh_start(events: list[tuple[int, float]]) -> bool:
    if len(events) < 2:
        return True
    step_increment = events[1][0] - events[0][0]
    return step_increment > 0 and events[0][0] == step_increment


def _concatenate_resume_chain(
    chain: list[list[tuple[int, float]]],
) -> list[tuple[int, float]]:
    result: list[tuple[int, float]] = []
    for i, events in enumerate(chain):
        next_first_step = chain[i + 1][0][0] if i + 1 < len(chain) else None
        for step, value in events:
            if next_first_step is not None and step >= next_first_step:
                break
            result.append((step, value))
    return result


def _smooth(values, window: int = 50) -> list[float]:
    if len(values) < window:
        return list(values)
    result = []
    for i in range(window - 1, len(values)):
        result.append(sum(values[i - window + 1: i + 1]) / window)
    return result


def _resolve_checkpoint(path: str | None) -> str | None:
    if path is not None:
        return path
    return _find_latest_checkpoint()


def _find_latest_checkpoint() -> str | None:
    checkpoint_dir = "model/checkpoints"
    if not os.path.exists(checkpoint_dir):
        return None
    best = os.path.join(checkpoint_dir, "best.pt")
    if os.path.exists(best):
        return best
    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith(".pt")]
    if not checkpoints:
        return None
    latest = max(checkpoints)
    return os.path.join(checkpoint_dir, latest)


def _ci_gate(results: list[BaselineResult]) -> None:
    always_accept = _find_result(results, "Always-Accept")
    rl_agent = _find_result(results, "RL Agent")

    if always_accept is None:
        logger.error("CI gate: Always-Accept baseline not found.")
        sys.exit(1)

    if rl_agent is None:
        logger.error("CI gate: RL Agent result not found — no checkpoint available.")
        sys.exit(1)

    if rl_agent.mean < always_accept.mean:
        logger.error(
            "CI gate FAILED: RL Agent mean (%.1f) < Always-Accept mean (%.1f)",
            rl_agent.mean, always_accept.mean,
        )
        sys.exit(1)

    logger.info(
        "CI gate PASSED: RL Agent mean (%.1f) >= Always-Accept mean (%.1f)",
        rl_agent.mean, always_accept.mean,
    )


def _find_result(results: list[BaselineResult], name: str) -> BaselineResult | None:
    return next((r for r in results if r.name == name), None)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RL agent against baselines")
    parser.add_argument("-n", "--num-games", type=int, default=1000, help="Games per agent")
    parser.add_argument("--checkpoint", type=str, default=None, help="RL checkpoint path")
    parser.add_argument("--log-dir", type=str, default="runs/doppelt_rl", help="TensorBoard log dir")
    parser.add_argument("--output-dir", type=str, default="evaluation_results", help="Output directory for plots")
    parser.add_argument("--ci", action="store_true", help="Fail if RL agent scores below Always-Accept")
    return parser.parse_args()


if __name__ == "__main__":
    main()
