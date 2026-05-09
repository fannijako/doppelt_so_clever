from __future__ import annotations

import os
import logging
import argparse
import statistics

from dataclasses import dataclass

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

from model.policy_network import PolicyNetwork

logger = logging.getLogger(__name__)


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

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    _plot_score_distributions(results, output_dir)
    _plot_learning_curve(args.log_dir, output_dir)

    logger.info("Evaluation complete. Plots saved to %s/", output_dir)


def _run_all_baselines(args: argparse.Namespace) -> list[BaselineResult]:
    results: list[BaselineResult] = []

    logger.info("Running random baseline (%d games)...", args.num_games)
    results.append(_run_baseline("Random", AutomaticInputHandler(), args.num_games))

    logger.info("Running always-accept baseline (%d games)...", args.num_games)
    results.append(_run_baseline("Always-Accept", AlwaysAcceptInputHandler(), args.num_games))

    checkpoint = _resolve_checkpoint(args.checkpoint)
    if checkpoint is not None:
        logger.info("Running RL agent (%d games) from %s...", args.num_games, checkpoint)
        results.append(_run_rl_agent(checkpoint, args.num_games))
    else:
        logger.warning("No checkpoint found — skipping RL agent evaluation.")

    return results


def _run_baseline(name: str, handler: InputHandler, num_games: int) -> BaselineResult:
    scores = [_play_standard_game(handler) for _ in range(num_games)]
    return BaselineResult(name=name, scores=scores)


def _play_standard_game(handler: InputHandler) -> int:
    board = Board()
    game = Game(
        input_handler=handler,
        board=board,
        observer=LoggingObserver(),
        action_handler=ActionHandler(board=board),
    )
    return game.play()


def _run_rl_agent(checkpoint_path: str, num_games: int) -> BaselineResult:
    policy = _load_policy(checkpoint_path)
    policy_fn = _create_policy_fn(policy)
    scores = [_play_rl_game(policy_fn) for _ in range(num_games)]
    return BaselineResult(name="RL Agent", scores=scores)


def _play_rl_game(policy_fn) -> int:
    board = Board()
    observer = RLObserver(board)
    handler = RLInputHandler(observer, policy_fn, training=False)
    game = Game(
        input_handler=handler,
        board=board,
        observer=observer,
        action_handler=ActionHandler(board=board),
    )
    return game.play()


def _load_policy(checkpoint_path: str) -> PolicyNetwork:
    policy = PolicyNetwork()
    checkpoint = torch.load(checkpoint_path, weights_only=True)
    policy.load_state_dict(checkpoint["policy_state_dict"])
    policy.eval()
    return policy


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


def _plot_score_distributions(results: list[BaselineResult], output_dir: str) -> None:
    fig, axes = plt.subplots(1, len(results), figsize=(6 * len(results), 5), sharey=True)
    if len(results) == 1:
        axes = [axes]

    for ax, result in zip(axes, results):
        _plot_single_distribution(ax, result)

    fig.suptitle("Score Distributions", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "score_distributions.png"), dpi=150)
    plt.close(fig)

    _plot_overlaid_distributions(results, output_dir)


def _plot_single_distribution(ax, result: BaselineResult) -> None:
    ax.hist(result.scores, bins=20, alpha=0.7, edgecolor="black")
    ax.set_title(f"{result.name}\n(mean={result.mean:.1f}, std={result.std:.1f})")
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency")
    _add_category_lines(ax)
    ax.set_xlim(0, 350)


def _plot_overlaid_distributions(results: list[BaselineResult], output_dir: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    for i, result in enumerate(results):
        ax.hist(
            result.scores, bins=30, alpha=0.5, label=f"{result.name} (μ={result.mean:.1f})",
            color=colors[i % len(colors)], edgecolor="black", linewidth=0.5,
        )
    _add_category_lines(ax)
    ax.set_xlim(0, 350)
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency")
    ax.set_title("Score Distributions — All Agents")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "score_distributions_overlay.png"), dpi=150)
    plt.close(fig)


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

    ea = EventAccumulator(log_dir)
    ea.Reload()

    tag = "score/mean"
    if tag not in ea.Tags().get("scalars", []):
        return []

    events = ea.Scalars(tag)
    return [(e.step, e.value) for e in events]


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
    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith(".pt")]
    if not checkpoints:
        return None
    latest = max(checkpoints)
    return os.path.join(checkpoint_dir, latest)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RL agent against baselines")
    parser.add_argument("-n", "--num-games", type=int, default=1000, help="Games per agent")
    parser.add_argument("--checkpoint", type=str, default=None, help="RL checkpoint path")
    parser.add_argument("--log-dir", type=str, default="runs/doppelt_rl", help="TensorBoard log dir")
    parser.add_argument("--output-dir", type=str, default="evaluation_results", help="Output directory for plots")
    return parser.parse_args()


if __name__ == "__main__":
    main()
