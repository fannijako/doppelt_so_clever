from __future__ import annotations

import argparse
import copy
import logging
import math
import os
import random
import time
from dataclasses import dataclass, field

import torch
from torch.utils.tensorboard import SummaryWriter

from model.policy_network import PolicyNetwork
from model.ppo import PPOConfig, PPOTrainer
from model.trajectory_buffer import build_batch
from model.rl_utils import DEFAULT_TERMINAL_REWARD_SCALE, EpisodeOptions, collect_batch
from src.board.board import Board
from src.game.reward_shaper import REWARD_MODE_CONFIGS
from src.game.rl_observer import RLObserver
from src.game.option_features import OPTION_FEATURE_SIZE

logger = logging.getLogger(__name__)


@dataclass
class ExploitConfig:
    fraction: float = 0.2
    perturb_factor: float = 1.2


@dataclass
class PBTIOConfig:
    checkpoint_dir: str = "model/pbt_checkpoints"
    log_dir: str = "runs/pbt"


@dataclass
class SharedHyperparams:
    augmented: bool = True
    strategic_features: bool = True
    reward_mode: str = "none"
    terminal_reward_scale: float = DEFAULT_TERMINAL_REWARD_SCALE
    gamma: float = 1.0
    gae_lambda: float = 0.95
    minibatch_size: int = 256


@dataclass
class PBTConfig:
    population_size: int = 8
    iterations: int = 5000
    eval_interval: int = 50
    eval_episodes: int = 32
    batch_size: int = 64
    num_workers: int = 0
    shared: SharedHyperparams = field(default_factory=SharedHyperparams)
    exploit: ExploitConfig = field(default_factory=ExploitConfig)
    io: PBTIOConfig = field(default_factory=PBTIOConfig)


@dataclass
class AgentConfig:
    learning_rate: float = 3e-4
    entropy_coefficient: float = 0.01
    hidden1: int = 256
    hidden2: int = 128
    shared: SharedHyperparams = field(default_factory=SharedHyperparams)


@dataclass
class Agent:
    idx: int
    policy: PolicyNetwork
    trainer: PPOTrainer
    config: AgentConfig
    mean_score: float = 0.0


def main() -> None:
    args = _parse_arguments()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )
    logging.getLogger("src").setLevel(logging.WARNING)
    pbt_config = _build_pbt_config(args)
    os.makedirs(pbt_config.io.checkpoint_dir, exist_ok=True)
    writer = SummaryWriter(log_dir=pbt_config.io.log_dir)

    population = _init_population(pbt_config)
    _pbt_loop(population, pbt_config, writer)

    _save_best(population, pbt_config.io.checkpoint_dir)
    writer.close()
    logger.info("PBT training complete.")


def _pbt_loop(
    population: list[Agent],
    config: PBTConfig,
    writer: SummaryWriter,
) -> None:
    for iteration in range(config.iterations):
        t0 = time.time()
        _train_step(population, config)
        elapsed = time.time() - t0
        logger.info("iter %d/%d  train_time=%.1fs", iteration + 1, config.iterations, elapsed)

        if (iteration + 1) % config.eval_interval == 0:
            _evaluate_population(population, config)
            _exploit_and_explore(population, config)
            _log_population(writer, iteration, population, elapsed)


def _train_step(population: list[Agent], config: PBTConfig) -> None:
    options = _shared_episode_options(config.shared)
    for agent in population:
        trajectories, _ = collect_batch(
            agent.policy, config.batch_size,
            options=options, num_workers=config.num_workers,
        )
        batch = build_batch(
            trajectories,
            gamma=config.shared.gamma, gae_lambda=config.shared.gae_lambda,
        )
        agent.trainer.update(batch)


def _evaluate_population(population: list[Agent], config: PBTConfig) -> None:
    options = _shared_episode_options(config.shared)
    for agent in population:
        _, scores = collect_batch(
            agent.policy, config.eval_episodes,
            options=options, num_workers=config.num_workers,
        )
        agent.mean_score = sum(scores) / len(scores)


def _shared_episode_options(shared: SharedHyperparams) -> EpisodeOptions:
    return EpisodeOptions(
        augmented=shared.augmented,
        terminal_reward_scale=shared.terminal_reward_scale,
        strategic_features=shared.strategic_features,
        reward_config=REWARD_MODE_CONFIGS[shared.reward_mode],
    )


def _exploit_and_explore(population: list[Agent], config: PBTConfig) -> None:
    ranked = sorted(population, key=lambda a: a.mean_score, reverse=True)
    cutoff = max(1, int(len(ranked) * config.exploit.fraction))
    top = ranked[:cutoff]
    bottom = ranked[-cutoff:]
    for weak in bottom:
        strong = random.choice(top)
        _copy_weights(source=strong, target=weak)
        _perturb_hyperparams(weak, config.exploit.perturb_factor)
        _rebuild_optimizer(weak)


def _copy_weights(source: Agent, target: Agent) -> None:
    target.policy.load_state_dict(copy.deepcopy(source.policy.state_dict()))


def _perturb_hyperparams(agent: Agent, factor: float) -> None:
    agent.config.learning_rate = _perturb_value(agent.config.learning_rate, factor, 1e-6, 1e-2)
    agent.config.entropy_coefficient = _perturb_value(
        agent.config.entropy_coefficient, factor, 1e-4, 0.1,
    )


def _perturb_value(value: float, factor: float, lo: float, hi: float) -> float:
    if random.random() < 0.5:
        value *= factor
    else:
        value /= factor
    return max(lo, min(hi, value))


def _rebuild_optimizer(agent: Agent) -> None:
    agent.trainer = PPOTrainer(agent.policy, _ppo_config_from(agent.config))


def _ppo_config_from(agent_config: AgentConfig) -> PPOConfig:
    return PPOConfig(
        learning_rate=agent_config.learning_rate,
        entropy_coefficient=agent_config.entropy_coefficient,
        gamma=agent_config.shared.gamma,
        gae_lambda=agent_config.shared.gae_lambda,
        minibatch_size=agent_config.shared.minibatch_size,
    )


def _init_population(config: PBTConfig) -> list[Agent]:
    return [_create_agent(i, config) for i in range(config.population_size)]


def _create_agent(idx: int, config: PBTConfig) -> Agent:
    lr = _sample_log_uniform(1e-4, 1e-3)
    ent = _sample_log_uniform(0.001, 0.05)
    agent_config = AgentConfig(
        learning_rate=lr, entropy_coefficient=ent, shared=config.shared,
    )
    policy = PolicyNetwork(
        state_size=_compute_pbt_state_size(config.shared),
        hidden1=agent_config.hidden1,
        hidden2=agent_config.hidden2,
    )
    trainer = PPOTrainer(policy, _ppo_config_from(agent_config))
    return Agent(idx=idx, policy=policy, trainer=trainer, config=agent_config)


def _compute_pbt_state_size(shared: SharedHyperparams) -> int:
    size = Board.STATE_SIZE + (
        RLObserver.AUGMENTED_CONTEXT_SIZE if shared.augmented else RLObserver.CONTEXT_SIZE
    )
    if shared.strategic_features:
        size += Board.STRATEGIC_FEATURES_SIZE
    return size


def _sample_log_uniform(low: float, high: float) -> float:
    return math.exp(random.uniform(math.log(low), math.log(high)))


def _log_population(
    writer: SummaryWriter,
    iteration: int,
    population: list[Agent],
    elapsed: float,
) -> None:
    scores = [a.mean_score for a in population]
    _log_population_summary(writer, iteration, scores, elapsed)
    _log_agent_hyperparams(writer, iteration, population)


def _log_population_summary(
    writer: SummaryWriter, iteration: int, scores: list[float], elapsed: float,
) -> None:
    best, mean, worst = max(scores), sum(scores) / len(scores), min(scores)
    logger.info(
        "PBT iter=%d  best=%.1f  mean=%.1f  worst=%.1f  time=%.1fs",
        iteration, best, mean, worst, elapsed,
    )
    writer.add_scalar("pbt/best_score", best, iteration)
    writer.add_scalar("pbt/mean_score", mean, iteration)
    writer.add_scalar("pbt/worst_score", worst, iteration)


def _log_agent_hyperparams(
    writer: SummaryWriter, iteration: int, population: list[Agent],
) -> None:
    for agent in population:
        writer.add_scalar(
            f"pbt/agent_{agent.idx}/lr",
            agent.config.learning_rate, iteration,
        )
        writer.add_scalar(
            f"pbt/agent_{agent.idx}/entropy_coef",
            agent.config.entropy_coefficient, iteration,
        )


def _save_best(population: list[Agent], checkpoint_dir: str) -> None:
    best = max(population, key=lambda a: a.mean_score)
    path = os.path.join(checkpoint_dir, "best_agent.pt")
    torch.save({
        "policy_state_dict": best.policy.state_dict(),
        "agent_config": {
            "learning_rate": best.config.learning_rate,
            "entropy_coefficient": best.config.entropy_coefficient,
            "hidden1": best.config.hidden1,
            "hidden2": best.config.hidden2,
        },
        "mean_score": best.mean_score,
        "state_size": _compute_pbt_state_size(best.config.shared),
        "augmented": best.config.shared.augmented,
        "strategic_features": best.config.shared.strategic_features,
        "strategic_features_version": Board.STRATEGIC_FEATURES_VERSION,
        "option_feature_size": OPTION_FEATURE_SIZE,
        "hidden1": best.config.hidden1,
        "hidden2": best.config.hidden2,
        "terminal_reward_scale": best.config.shared.terminal_reward_scale,
        "gamma": best.config.shared.gamma,
        "gae_lambda": best.config.shared.gae_lambda,
        "reward_mode": best.config.shared.reward_mode,
    }, path)
    logger.info("Saved best agent (score=%.1f) to %s", best.mean_score, path)


def _build_pbt_config(args: argparse.Namespace) -> PBTConfig:
    return PBTConfig(
        population_size=args.population_size,
        iterations=args.iterations,
        eval_interval=args.eval_interval,
        eval_episodes=args.eval_episodes,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        shared=SharedHyperparams(
            augmented=args.augmented,
            strategic_features=args.strategic_features,
            reward_mode=args.reward_mode,
            terminal_reward_scale=args.terminal_reward_scale,
            gamma=args.gamma,
            gae_lambda=args.gae_lambda,
            minibatch_size=args.minibatch_size,
        ),
        exploit=ExploitConfig(
            fraction=args.exploit_fraction,
            perturb_factor=args.perturb_factor,
        ),
        io=PBTIOConfig(
            checkpoint_dir=args.checkpoint_dir,
            log_dir=args.log_dir,
        ),
    )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Population-Based Training for Doppelt so clever",
    )
    _add_pbt_core_args(parser)
    _add_pbt_exploit_args(parser)
    _add_pbt_io_args(parser)
    _add_pbt_shared_args(parser)
    return parser.parse_args()


def _add_pbt_core_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--population-size", type=int, default=8)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--eval-interval", type=int, default=50)
    parser.add_argument("--eval-episodes", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=0, help="Parallel episode workers (0=sequential)")


def _add_pbt_exploit_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--exploit-fraction", type=float, default=0.2)
    parser.add_argument("--perturb-factor", type=float, default=1.2)


def _add_pbt_io_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint-dir", type=str, default="model/pbt_checkpoints")
    parser.add_argument("--log-dir", type=str, default="runs/pbt")


def _add_pbt_shared_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--augmented", action=argparse.BooleanOptionalAction, default=True,
        help="Enable observation augmentation. Default on; use --no-augmented to disable.",
    )
    parser.add_argument(
        "--strategic-features", action=argparse.BooleanOptionalAction, default=True,
        help="Append derived strategic features (Phase 1). Default on; use --no-strategic-features for ablation.",
    )
    parser.add_argument(
        "--reward-mode", choices=tuple(REWARD_MODE_CONFIGS), default="none",
        help=(
            "Per-step reward shaping: none (default, sparse terminal only), "
            "total (legacy breadth shaping), min-section (PBRS on the weakest section)."
        ),
    )
    parser.add_argument("--gamma", type=float, default=1.0, help="Discount factor for GAE")
    parser.add_argument("--gae-lambda", type=float, default=0.95, help="GAE lambda")
    parser.add_argument("--minibatch-size", type=int, default=256, help="PPO minibatch size")
    parser.add_argument(
        "--terminal-reward-scale", type=float, default=DEFAULT_TERMINAL_REWARD_SCALE,
        help="Multiplier applied to the terminal score reward (default 1/10)",
    )


if __name__ == "__main__":
    main()
