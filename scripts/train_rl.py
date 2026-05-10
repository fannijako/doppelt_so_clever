from __future__ import annotations

import argparse
import logging
import os
import time
from dataclasses import dataclass, field

import torch
from torch.utils.tensorboard import SummaryWriter

from model.policy_network import PolicyNetwork, STATE_SIZE
from model.ppo import PPOConfig, PPOTrainer, PPOUpdateResult
from model.trajectory_buffer import build_batch
from model.rl_utils import collect_batch
from src.game.rl_observer import PROMPT_FEATURES_SIZE

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlags:
    augmented: bool = False
    lr_decay: bool = False
    curriculum: bool = False
    max_rounds_start: int = 2
    max_rounds_end: int = 6


@dataclass
class IOConfig:
    checkpoint_interval: int = 100
    checkpoint_dir: str = "model/checkpoints"
    log_dir: str = "runs/doppelt_rl"
    resume: str | None = None


@dataclass
class TrainingConfig:
    iterations: int = 5000
    batch_size: int = 64
    ppo: PPOConfig = field(default_factory=PPOConfig)
    hidden1: int = 256
    hidden2: int = 128
    features: FeatureFlags = field(default_factory=FeatureFlags)
    io: IOConfig = field(default_factory=IOConfig)


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
    for iteration in range(start_iteration, config.iterations):
        result, metrics = _training_step(ctx, config, iteration)
        _log_iteration(writer, metrics, result)
        _maybe_checkpoint(ctx.policy, ctx.trainer, iteration, config)
    _save_checkpoint(ctx.policy, ctx.trainer, config.iterations - 1, config.io.checkpoint_dir)


def _training_step(
    ctx: TrainingContext,
    config: TrainingConfig,
    iteration: int,
) -> tuple[PPOUpdateResult, IterationMetrics]:
    t0 = time.time()
    max_rounds = _curriculum_rounds(iteration, config)
    trajectories, scores = collect_batch(
        ctx.policy, config.batch_size,
        config.features.augmented, max_rounds,
    )
    batch = build_batch(trajectories)
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
        _save_checkpoint(policy, trainer, iteration, config.io.checkpoint_dir)


def _save_checkpoint(
    policy: PolicyNetwork,
    trainer: PPOTrainer,
    iteration: int,
    checkpoint_dir: str,
) -> None:
    path = os.path.join(checkpoint_dir, f"checkpoint_{iteration:06d}.pt")
    torch.save({
        "iteration": iteration,
        "policy_state_dict": policy.state_dict(),
        "optimizer_state_dict": trainer.optimizer.state_dict(),
    }, path)
    logger.info("Saved checkpoint: %s", path)


def _load_checkpoint(
    path: str,
    policy: PolicyNetwork,
    trainer: PPOTrainer,
) -> int:
    checkpoint = torch.load(path, weights_only=True)
    policy.load_state_dict(checkpoint["policy_state_dict"])
    trainer.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    start_iteration = checkpoint["iteration"] + 1
    logger.info("Resumed from %s (iteration %d)", path, start_iteration)
    return start_iteration


def _compute_state_size(augmented: bool) -> int:
    if augmented:
        return STATE_SIZE + PROMPT_FEATURES_SIZE
    return STATE_SIZE


def _setup_model(
    config: TrainingConfig,
) -> tuple[PolicyNetwork, PPOTrainer, int]:
    state_size = _compute_state_size(config.features.augmented)
    policy = PolicyNetwork(
        state_size=state_size, hidden1=config.hidden1, hidden2=config.hidden2,
    )
    trainer = PPOTrainer(policy, config.ppo)
    start_iteration = 0
    if config.io.resume:
        start_iteration = _load_checkpoint(config.io.resume, policy, trainer)
    return policy, trainer, start_iteration


def _build_config(args: argparse.Namespace) -> TrainingConfig:
    ppo = PPOConfig(
        learning_rate=args.lr,
        epochs_per_batch=args.ppo_epochs,
        entropy_coefficient=args.entropy_coef,
        value_loss_coefficient=args.value_coef,
    )
    features = FeatureFlags(
        augmented=args.augmented,
        lr_decay=args.lr_decay,
        curriculum=args.curriculum,
        max_rounds_start=args.max_rounds_start,
        max_rounds_end=args.max_rounds_end,
    )
    io_config = IOConfig(
        checkpoint_interval=args.checkpoint_interval,
        checkpoint_dir=args.checkpoint_dir,
        log_dir=args.log_dir,
        resume=args.resume,
    )
    return TrainingConfig(
        iterations=args.iterations,
        batch_size=args.batch_size,
        ppo=ppo,
        hidden1=args.hidden1,
        hidden2=args.hidden2,
        features=features,
        io=io_config,
    )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train RL agent for Doppelt so clever")
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--ppo-epochs", type=int, default=4)
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--value-coef", type=float, default=0.5)
    parser.add_argument("--checkpoint-interval", type=int, default=100)
    parser.add_argument("--checkpoint-dir", type=str, default="model/checkpoints")
    parser.add_argument("--log-dir", type=str, default="runs/doppelt_rl")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")
    parser.add_argument("--hidden1", type=int, default=256, help="First hidden layer size")
    parser.add_argument("--hidden2", type=int, default=128, help="Second hidden layer size")
    parser.add_argument("--lr-decay", action="store_true", help="Enable linear learning rate decay")
    parser.add_argument("--augmented", action="store_true", help="Enable observation augmentation (prompt type encoding)")
    parser.add_argument("--curriculum", action="store_true", help="Enable curriculum learning (gradual round increase)")
    parser.add_argument("--max-rounds-start", type=int, default=2, help="Starting number of rounds for curriculum")
    parser.add_argument("--max-rounds-end", type=int, default=6, help="Final number of rounds for curriculum")
    return parser.parse_args()


if __name__ == "__main__":
    main()
