from __future__ import annotations

import argparse
import logging
import os
import time
from dataclasses import dataclass, field

import torch
from torch.utils.tensorboard import SummaryWriter

from model.policy_network import PolicyNetwork
from model.ppo import PPOConfig, PPOTrainer, PPOUpdateResult
from model.trajectory_buffer import build_batch
from model.early_stop import EarlyStopConfig, EarlyStopTracker
from model.rl_utils import DEFAULT_TERMINAL_REWARD_SCALE, EpisodeOptions, collect_batch
from src.board.board import Board
from src.game.reward_shaper import REWARD_MODE_CONFIGS
from src.game.rl_observer import RLObserver
from src.game.option_features import OPTION_FEATURE_SIZE

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlags:  # pylint: disable=too-many-instance-attributes
    augmented: bool = True
    lr_decay: bool = False
    curriculum: bool = False
    max_rounds_start: int = 2
    max_rounds_end: int = 6
    reward_mode: str = "none"
    curriculum_eval_episodes: int = 16
    terminal_reward_scale: float = DEFAULT_TERMINAL_REWARD_SCALE
    strategic_features: bool = True


@dataclass
class IOConfig:
    checkpoint_interval: int = 100
    checkpoint_dir: str = "model/checkpoints"
    log_dir: str = "runs/doppelt_rl"
    resume: str | None = None


@dataclass
class EvalConfig:
    interval: int = 50
    episodes: int = 32


@dataclass
class ModelConfig:
    hidden1: int = 256
    hidden2: int = 128


@dataclass
class TrainingConfig:
    iterations: int = 5000
    batch_size: int = 64
    num_workers: int = 0
    ppo: PPOConfig = field(default_factory=PPOConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    io: IOConfig = field(default_factory=IOConfig)
    early_stop: EarlyStopConfig = field(default_factory=EarlyStopConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)


@dataclass
class IterationMetrics:
    iteration: int
    global_episode: int
    scores: list[int]
    elapsed: float


@dataclass
class TrainingContext:
    policy: PolicyNetwork
    trainer: PPOTrainer
    scheduler: torch.optim.lr_scheduler.LRScheduler | None = None


def main() -> None:
    args = _parse_arguments()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = _build_config(args)
    policy, trainer, start_iteration = _setup_model(config)
    writer = SummaryWriter(log_dir=config.io.log_dir)
    os.makedirs(config.io.checkpoint_dir, exist_ok=True)

    ctx = TrainingContext(
        policy=policy, trainer=trainer,
        scheduler=_build_scheduler(trainer, config),
    )
    _training_loop(ctx, writer, config, start_iteration)

    writer.close()
    logger.info("Training complete.")


def _training_loop(
    ctx: TrainingContext,
    writer: SummaryWriter,
    config: TrainingConfig,
    start_iteration: int,
) -> None:
    tracker = EarlyStopTracker(
        patience=config.early_stop.patience,
        smoothing=config.early_stop.smoothing,
    )
    best_eval_score = float("-inf")
    last_iteration = start_iteration
    for iteration in range(start_iteration, config.iterations):
        result, metrics = _training_step(ctx, config, iteration)
        _log_iteration(writer, metrics, result)
        _maybe_checkpoint(ctx.policy, ctx.trainer, iteration, config)
        best_eval_score = _maybe_eval_and_save_best(
            ctx, config, iteration, best_eval_score, writer,
        )
        last_iteration = iteration
        if _check_early_stop(tracker, metrics, ctx.policy, config):
            break
    _save_checkpoint(ctx.policy, ctx.trainer, last_iteration, config)


def _check_early_stop(
    tracker: EarlyStopTracker,
    metrics: IterationMetrics,
    policy: PolicyNetwork,
    config: TrainingConfig,
) -> bool:
    if not tracker.enabled:
        return False
    score = _early_stop_score(metrics, policy, config)
    if tracker.step(score, policy.state_dict()):
        logger.info("Restoring best weights (smoothed score: %.1f)", tracker.best_score)
        policy.load_state_dict(tracker.best_state())
        return True
    return False


def _early_stop_score(
    metrics: IterationMetrics,
    policy: PolicyNetwork,
    config: TrainingConfig,
) -> float:
    if config.features.curriculum:
        return _full_round_eval(policy, config)
    return sum(metrics.scores) / len(metrics.scores)


def _full_round_eval(policy: PolicyNetwork, config: TrainingConfig) -> float:
    n = config.features.curriculum_eval_episodes
    _, scores = collect_batch(
        policy, n,
        options=_episode_options(config, max_rounds=None),
        num_workers=config.num_workers,
    )
    mean = sum(scores) / len(scores)
    logger.info("Curriculum full-round eval (%d games): mean=%.1f", n, mean)
    return mean


def _episode_options(config: TrainingConfig, max_rounds: int | None) -> EpisodeOptions:
    return EpisodeOptions(
        augmented=config.features.augmented,
        max_rounds=max_rounds,
        terminal_reward_scale=config.features.terminal_reward_scale,
        reward_config=REWARD_MODE_CONFIGS[config.features.reward_mode],
        strategic_features=config.features.strategic_features,
    )


def _training_step(
    ctx: TrainingContext,
    config: TrainingConfig,
    iteration: int,
) -> tuple[PPOUpdateResult, IterationMetrics]:
    t0 = time.time()
    max_rounds = _curriculum_rounds(iteration, config)
    trajectories, scores = collect_batch(
        ctx.policy, config.batch_size,
        options=_episode_options(config, max_rounds),
        num_workers=config.num_workers,
    )
    batch = build_batch(
        trajectories, gamma=config.ppo.gamma, gae_lambda=config.ppo.gae_lambda,
    )
    result = ctx.trainer.update(batch)
    if ctx.scheduler is not None:
        ctx.scheduler.step()
    metrics = IterationMetrics(
        iteration=iteration,
        global_episode=(iteration + 1) * config.batch_size,
        scores=scores,
        elapsed=time.time() - t0,
    )
    return result, metrics


def _build_scheduler(
    trainer: PPOTrainer, config: TrainingConfig,
) -> torch.optim.lr_scheduler.LRScheduler | None:
    if not config.features.lr_decay:
        return None
    return torch.optim.lr_scheduler.LinearLR(
        trainer.optimizer,
        start_factor=1.0,
        end_factor=0.0,
        total_iters=config.iterations,
    )


def _curriculum_rounds(iteration: int, config: TrainingConfig) -> int | None:
    if not config.features.curriculum:
        return None
    progress = iteration / max(config.iterations - 1, 1)
    span = config.features.max_rounds_end - config.features.max_rounds_start
    return config.features.max_rounds_start + int(progress * span)


def _log_iteration(
    writer: SummaryWriter,
    metrics: IterationMetrics,
    result: PPOUpdateResult,
) -> None:
    mean_s, min_s, max_s = _score_stats(metrics.scores)
    logger.info(
        "iter=%d  episodes=%d  score=%.1f/%.0f/%.0f  "
        "ploss=%.4f  vloss=%.4f  ent=%.4f  time=%.1fs",
        metrics.iteration, metrics.global_episode, mean_s, min_s, max_s,
        result.policy_loss, result.value_loss, result.entropy, metrics.elapsed,
    )
    _write_scalars(writer, metrics.global_episode, {
        "score/mean": mean_s, "score/min": min_s, "score/max": max_s,
        "loss/policy": result.policy_loss, "loss/value": result.value_loss,
        "loss/total": result.total_loss, "loss/entropy": result.entropy,
    })


def _score_stats(scores: list[int]) -> tuple[float, int, int]:
    return sum(scores) / len(scores), min(scores), max(scores)


def _write_scalars(
    writer: SummaryWriter,
    step: int,
    scalars: dict[str, float],
) -> None:
    for tag, value in scalars.items():
        writer.add_scalar(tag, value, step)


def _maybe_checkpoint(
    policy: PolicyNetwork,
    trainer: PPOTrainer,
    iteration: int,
    config: TrainingConfig,
) -> None:
    if (iteration + 1) % config.io.checkpoint_interval == 0:
        _save_checkpoint(policy, trainer, iteration, config)


def _maybe_eval_and_save_best(
    ctx: TrainingContext,
    config: TrainingConfig,
    iteration: int,
    best_eval_score: float,
    writer: SummaryWriter,
) -> float:
    if config.eval.interval <= 0 or (iteration + 1) % config.eval.interval != 0:
        return best_eval_score
    score = _evaluate_policy(ctx.policy, config)
    writer.add_scalar("eval/mean_score", score, (iteration + 1) * config.batch_size)
    logger.info(
        "eval iter=%d  mean=%.1f  best=%.1f",
        iteration, score, max(best_eval_score, score),
    )
    if score > best_eval_score:
        _save_best_checkpoint(ctx.policy, ctx.trainer, iteration, score, config)
        return score
    return best_eval_score


def _evaluate_policy(policy: PolicyNetwork, config: TrainingConfig) -> float:
    _, scores = collect_batch(
        policy, config.eval.episodes,
        options=_episode_options(config, max_rounds=None),
        num_workers=config.num_workers,
    )
    return sum(scores) / len(scores)


def _save_best_checkpoint(
    policy: PolicyNetwork,
    trainer: PPOTrainer,
    iteration: int,
    eval_score: float,
    config: TrainingConfig,
) -> None:
    path = os.path.join(config.io.checkpoint_dir, "best.pt")
    payload = _checkpoint_payload(policy, trainer, iteration, config)
    payload["best_eval_score"] = eval_score
    payload["best_eval_iteration"] = iteration
    torch.save(payload, path)
    logger.info("Saved new best checkpoint (score=%.1f): %s", eval_score, path)


def _save_checkpoint(
    policy: PolicyNetwork,
    trainer: PPOTrainer,
    iteration: int,
    config: TrainingConfig,
) -> None:
    path = os.path.join(config.io.checkpoint_dir, f"checkpoint_{iteration:06d}.pt")
    torch.save(_checkpoint_payload(policy, trainer, iteration, config), path)
    logger.info("Saved checkpoint: %s", path)


def _checkpoint_payload(
    policy: PolicyNetwork,
    trainer: PPOTrainer,
    iteration: int,
    config: TrainingConfig,
) -> dict:
    return {
        "iteration": iteration,
        "policy_state_dict": policy.state_dict(),
        "optimizer_state_dict": trainer.optimizer.state_dict(),
        "state_size": _compute_state_size(
            config.features.augmented, config.features.strategic_features,
        ),
        "augmented": config.features.augmented,
        "strategic_features": config.features.strategic_features,
        "strategic_features_version": Board.STRATEGIC_FEATURES_VERSION,
        "option_feature_size": OPTION_FEATURE_SIZE,
        "hidden1": config.model.hidden1,
        "hidden2": config.model.hidden2,
        "terminal_reward_scale": config.features.terminal_reward_scale,
        "gamma": config.ppo.gamma,
        "gae_lambda": config.ppo.gae_lambda,
        "reward_mode": config.features.reward_mode,
    }


def _load_checkpoint(
    path: str,
    policy: PolicyNetwork,
    trainer: PPOTrainer,
    config: TrainingConfig,
) -> int:
    checkpoint = torch.load(path, weights_only=True)
    require_phase3_metadata(checkpoint, path)
    _assert_resume_feature_parity(checkpoint, config, path)
    policy.load_state_dict(checkpoint["policy_state_dict"])
    trainer.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    start_iteration = checkpoint["iteration"] + 1
    logger.info("Resumed from %s (iteration %d)", path, start_iteration)
    return start_iteration


_PHASE3_METADATA_ERROR = (
    "Checkpoint missing required Phase 3 metadata (state_size, augmented). "
    "Regenerate the checkpoint after Phase 3."
)


def require_phase3_metadata(checkpoint: dict, path: str) -> None:
    if "state_size" not in checkpoint or "augmented" not in checkpoint:
        raise ValueError(f"{_PHASE3_METADATA_ERROR} Checkpoint: {path}")


def checkpoint_strategic_features(checkpoint: dict) -> bool:
    return checkpoint.get("strategic_features", False)


def assert_observer_state_size(observer: RLObserver, expected_state_size: int, source: str = "") -> None:
    if observer.state_size != expected_state_size:
        raise ValueError(
            f"Observer state size {observer.state_size} does not match the loaded network "
            f"input size {expected_state_size} (augmented={observer.augmented}, "
            f"strategic_features={observer.strategic_features_enabled}). {source}".strip()
        )


def _assert_resume_feature_parity(checkpoint: dict, config: TrainingConfig, path: str) -> None:
    expected = _compute_state_size(
        config.features.augmented, config.features.strategic_features,
    )
    if checkpoint["state_size"] != expected:
        raise ValueError(
            f"Cannot resume: checkpoint state size {checkpoint['state_size']} does not match "
            f"the configured state size {expected} (augmented={config.features.augmented}, "
            f"strategic_features={config.features.strategic_features}). Checkpoint: {path}"
        )


def _compute_state_size(augmented: bool, strategic_features: bool) -> int:
    size = Board.STATE_SIZE + (
        RLObserver.AUGMENTED_CONTEXT_SIZE if augmented else RLObserver.CONTEXT_SIZE
    )
    if strategic_features:
        size += Board.STRATEGIC_FEATURES_SIZE
    return size


def _setup_model(
    config: TrainingConfig,
) -> tuple[PolicyNetwork, PPOTrainer, int]:
    state_size = _compute_state_size(
        config.features.augmented, config.features.strategic_features,
    )
    policy = PolicyNetwork(
        state_size=state_size, hidden1=config.model.hidden1, hidden2=config.model.hidden2,
    )
    trainer = PPOTrainer(policy, config.ppo)
    start_iteration = 0
    if config.io.resume:
        start_iteration = _load_checkpoint(config.io.resume, policy, trainer, config)
    return policy, trainer, start_iteration


def _build_config(args: argparse.Namespace) -> TrainingConfig:
    _validate_args(args)
    ppo = PPOConfig(
        learning_rate=args.lr,
        epochs_per_batch=args.ppo_epochs,
        entropy_coefficient=args.entropy_coef,
        value_loss_coefficient=args.value_coef,
        minibatch_size=args.minibatch_size,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
    )
    features = FeatureFlags(
        augmented=args.augmented,
        lr_decay=args.lr_decay,
        curriculum=args.curriculum,
        max_rounds_start=args.max_rounds_start,
        max_rounds_end=args.max_rounds_end,
        reward_mode=args.reward_mode,
        curriculum_eval_episodes=args.curriculum_eval_episodes,
        terminal_reward_scale=args.terminal_reward_scale,
        strategic_features=args.strategic_features,
    )
    io_config = IOConfig(
        checkpoint_interval=args.checkpoint_interval,
        checkpoint_dir=args.checkpoint_dir,
        log_dir=args.log_dir,
        resume=args.resume,
    )
    early_stop = EarlyStopConfig(
        patience=args.early_stop_patience,
        smoothing=args.early_stop_smoothing,
    )
    eval_config = EvalConfig(
        interval=args.eval_interval,
        episodes=args.eval_episodes,
    )
    return TrainingConfig(
        iterations=args.iterations,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        ppo=ppo,
        model=ModelConfig(hidden1=args.hidden1, hidden2=args.hidden2),
        features=features,
        io=io_config,
        early_stop=early_stop,
        eval=eval_config,
    )


def _validate_args(args: argparse.Namespace) -> None:
    if args.curriculum and args.reward_mode == "none":
        raise ValueError(
            "curriculum requires a per-step reward signal. "
            "Use --reward-mode total or --reward-mode min-section, or drop --curriculum.",
        )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train RL agent for Doppelt so clever")
    _add_core_args(parser)
    _add_ppo_args(parser)
    _add_io_args(parser)
    _add_feature_args(parser)
    _add_reward_args(parser)
    return parser.parse_args()


def _add_core_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=0, help="Parallel episode workers (0=sequential)")
    parser.add_argument("--hidden1", type=int, default=256, help="First hidden layer size")
    parser.add_argument("--hidden2", type=int, default=128, help="Second hidden layer size")


def _add_ppo_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--ppo-epochs", type=int, default=4)
    parser.add_argument("--entropy-coef", type=float, default=0.05)
    parser.add_argument("--value-coef", type=float, default=0.5)
    parser.add_argument("--gamma", type=float, default=1.0, help="Discount factor for GAE")
    parser.add_argument("--gae-lambda", type=float, default=0.95, help="GAE lambda")
    parser.add_argument("--minibatch-size", type=int, default=256, help="PPO minibatch size")
    parser.add_argument("--lr-decay", action="store_true", help="Enable linear learning rate decay")


def _add_io_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint-interval", type=int, default=100)
    parser.add_argument("--checkpoint-dir", type=str, default="model/checkpoints")
    parser.add_argument("--log-dir", type=str, default="runs/doppelt_rl")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")
    parser.add_argument("--early-stop-patience", type=int, default=0, help="Early stop patience in iterations (0=disabled)")
    parser.add_argument("--early-stop-smoothing", type=float, default=0.05, help="EMA smoothing factor for early stop score")
    parser.add_argument(
        "--eval-interval", type=int, default=50,
        help="Iterations between best-by-eval checkpoints (0=disabled)",
    )
    parser.add_argument(
        "--eval-episodes", type=int, default=32,
        help="Full-round episodes per eval pass for best.pt",
    )


def _add_feature_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--augmented", action=argparse.BooleanOptionalAction, default=True,
        help="Enable observation augmentation (prompt + option features). Default on; use --no-augmented to disable.",
    )
    parser.add_argument(
        "--strategic-features", action=argparse.BooleanOptionalAction, default=True,
        help="Append derived strategic features (Phase 1). Default on; use --no-strategic-features for ablation.",
    )
    parser.add_argument("--curriculum", action="store_true", help="Enable curriculum learning (gradual round increase)")
    parser.add_argument("--max-rounds-start", type=int, default=2, help="Starting number of rounds for curriculum")
    parser.add_argument("--max-rounds-end", type=int, default=6, help="Final number of rounds for curriculum")
    parser.add_argument(
        "--curriculum-eval-episodes", type=int, default=16,
        help="Full 6-round episodes used to score the policy for early-stop when curriculum is on.",
    )


def _add_reward_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--terminal-reward-scale", type=float, default=DEFAULT_TERMINAL_REWARD_SCALE,
        help="Multiplier applied to the terminal score reward (default 1/10)",
    )
    parser.add_argument(
        "--reward-mode", choices=tuple(REWARD_MODE_CONFIGS), default="none",
        help=(
            "Per-step reward shaping: none (default, sparse terminal only), "
            "total (legacy breadth shaping), min-section (PBRS on the weakest section)."
        ),
    )


if __name__ == "__main__":
    main()
