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
from model.trajectory_buffer import (
    Trajectory,
    Transition as BufferTransition,
    build_batch,
)
from src.actions.action_handler import ActionHandler
from src.board.board import Board
from src.game.game import Game
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler, Transition

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    iterations: int = 5000
    batch_size: int = 64
    ppo: PPOConfig = field(default_factory=PPOConfig)
    checkpoint_interval: int = 100
    checkpoint_dir: str = "model/checkpoints"
    log_dir: str = "runs/doppelt_rl"
    resume: str | None = None


@dataclass
class IterationMetrics:
    iteration: int
    global_episode: int
    scores: list[int]
    elapsed: float


def main() -> None:
    args = _parse_arguments()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = _build_config(args)
    policy, trainer, start_iteration = _setup_model(config)
    writer = SummaryWriter(log_dir=config.log_dir)
    os.makedirs(config.checkpoint_dir, exist_ok=True)

    _training_loop(policy, trainer, writer, config, start_iteration)

    writer.close()
    logger.info("Training complete.")


def _training_loop(
    policy: PolicyNetwork,
    trainer: PPOTrainer,
    writer: SummaryWriter,
    config: TrainingConfig,
    start_iteration: int,
) -> None:
    for iteration in range(start_iteration, config.iterations):
        t0 = time.time()
        trajectories, scores = _collect_batch(policy, config.batch_size)
        batch = build_batch(trajectories)
        result = trainer.update(batch)
        elapsed = time.time() - t0

        metrics = IterationMetrics(
            iteration=iteration,
            global_episode=(iteration + 1) * config.batch_size,
            scores=scores,
            elapsed=elapsed,
        )
        _log_iteration(writer, metrics, result)
        _maybe_checkpoint(policy, trainer, iteration, config)

    _save_checkpoint(policy, trainer, config.iterations - 1, config.checkpoint_dir)


def _collect_batch(
    policy: PolicyNetwork,
    batch_size: int,
) -> tuple[list[Trajectory], list[int]]:
    policy_fn = _make_policy_fn(policy)
    trajectories: list[Trajectory] = []
    scores: list[int] = []
    for _ in range(batch_size):
        traj, score = _run_episode(policy_fn)
        trajectories.append(traj)
        scores.append(score)
    return trajectories, scores


def _run_episode(policy_fn) -> tuple[Trajectory, int]:
    board = Board()
    observer = RLObserver(board)
    handler = RLInputHandler(observer, policy_fn, training=True)
    game = Game(
        input_handler=handler,
        board=board,
        observer=observer,
        action_handler=ActionHandler(board=board),
    )
    score = game.play()
    return _convert_trajectory(handler.trajectory, float(score)), score


def _convert_trajectory(transitions: list[Transition], reward: float) -> Trajectory:
    traj = Trajectory(reward=reward)
    for t in transitions:
        traj.append(BufferTransition(
            state=t.state,
            action=t.action,
            log_prob=t.log_prob,
            value=t.value,
            action_mask=[float(m) for m in t.action_mask],
        ))
    return traj


def _make_policy_fn(policy: PolicyNetwork):
    @torch.no_grad()
    def policy_fn(
        state: list[float], action_mask: list[bool]
    ) -> tuple[int, float, float]:
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        mask_t = torch.tensor(
            [float(m) for m in action_mask], dtype=torch.float32
        ).unsqueeze(0)
        action, log_prob, _, value = policy.get_action_and_value(state_t, mask_t)
        return action.item(), log_prob.item(), value.item()

    return policy_fn


def _log_iteration(
    writer: SummaryWriter,
    metrics: IterationMetrics,
    result: PPOUpdateResult,
) -> None:
    mean_score = sum(metrics.scores) / len(metrics.scores)
    min_score = min(metrics.scores)
    max_score = max(metrics.scores)

    logger.info(
        "iter=%d  episodes=%d  score=%.1f/%.0f/%.0f  "
        "ploss=%.4f  vloss=%.4f  ent=%.4f  time=%.1fs",
        metrics.iteration, metrics.global_episode, mean_score, min_score, max_score,
        result.policy_loss, result.value_loss, result.entropy, metrics.elapsed,
    )

    _write_scalars(writer, metrics.global_episode, {
        "score/mean": mean_score,
        "score/min": min_score,
        "score/max": max_score,
        "loss/policy": result.policy_loss,
        "loss/value": result.value_loss,
        "loss/total": result.total_loss,
        "loss/entropy": result.entropy,
    })


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
    if (iteration + 1) % config.checkpoint_interval == 0:
        _save_checkpoint(policy, trainer, iteration, config.checkpoint_dir)


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


def _setup_model(
    config: TrainingConfig,
) -> tuple[PolicyNetwork, PPOTrainer, int]:
    policy = PolicyNetwork()
    trainer = PPOTrainer(policy, config.ppo)
    start_iteration = 0
    if config.resume:
        start_iteration = _load_checkpoint(config.resume, policy, trainer)
    return policy, trainer, start_iteration


def _build_config(args: argparse.Namespace) -> TrainingConfig:
    ppo = PPOConfig(
        learning_rate=args.lr,
        epochs_per_batch=args.ppo_epochs,
        entropy_coefficient=args.entropy_coef,
        value_loss_coefficient=args.value_coef,
    )
    return TrainingConfig(
        iterations=args.iterations,
        batch_size=args.batch_size,
        ppo=ppo,
        checkpoint_interval=args.checkpoint_interval,
        checkpoint_dir=args.checkpoint_dir,
        log_dir=args.log_dir,
        resume=args.resume,
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
    return parser.parse_args()


if __name__ == "__main__":
    main()
