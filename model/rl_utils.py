from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import get_context

import torch

from model.policy_network import PolicyNetwork
from model.trajectory_buffer import Trajectory, Transition as BufferTransition
from src.actions.action_handler import ActionHandler
from src.board.board import Board
from src.game.game import Game
from src.game.reward_shaper import RewardConfig
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler, Transition

DEFAULT_TERMINAL_REWARD_SCALE = 1.0 / 10.0

_WORKER_STATE: dict = {}


@dataclass(frozen=True)
class EpisodeOptions:
    augmented: bool = True
    max_rounds: int | None = None
    terminal_reward_scale: float = DEFAULT_TERMINAL_REWARD_SCALE
    reward_config: RewardConfig | None = None
    strategic_features: bool = False


def make_policy_fn(policy: PolicyNetwork):
    @torch.no_grad()
    def policy_fn(
        state: list[float], action_mask: list[bool],
    ) -> tuple[int, float, float]:
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        mask_t = torch.tensor(
            [float(m) for m in action_mask], dtype=torch.float32,
        ).unsqueeze(0)
        action, log_prob, _, value = policy.get_action_and_value(state_t, mask_t)
        return action.item(), log_prob.item(), value.item()

    return policy_fn


def convert_trajectory(transitions: list[Transition], reward: float) -> Trajectory:
    traj = Trajectory(reward=reward)
    for t in transitions:
        traj.append(BufferTransition(
            state=t.state,
            action=t.action,
            log_prob=t.log_prob,
            value=t.value,
            action_mask=[float(m) for m in t.action_mask],
            reward=t.reward,
        ))
    return traj


def run_episode(
    policy_fn,
    options: EpisodeOptions | None = None,
    training: bool = True,
) -> tuple[Trajectory, int]:
    opts = options or EpisodeOptions()
    board = Board()
    observer = RLObserver(
        board, augmented=opts.augmented, strategic_features=opts.strategic_features,
    )
    handler = RLInputHandler(
        observer, policy_fn, training=training, reward_config=opts.reward_config,
    )
    game = Game(
        input_handler=handler,
        board=board,
        observer=observer,
        action_handler=ActionHandler(board=board),
    )
    score = game.play(max_rounds=opts.max_rounds)
    handler.flush_terminal_step_reward()
    scaled_terminal = float(score) * opts.terminal_reward_scale
    return convert_trajectory(handler.trajectory, scaled_terminal), score


def collect_batch(
    policy: PolicyNetwork,
    batch_size: int,
    options: EpisodeOptions | None = None,
    num_workers: int = 0,
) -> tuple[list[Trajectory], list[int]]:
    opts = options or EpisodeOptions()
    if num_workers <= 1:
        return _collect_sequential(policy, batch_size, opts)
    return _collect_parallel(policy, batch_size, opts, num_workers)


def _collect_sequential(
    policy: PolicyNetwork,
    batch_size: int,
    options: EpisodeOptions,
) -> tuple[list[Trajectory], list[int]]:
    policy_fn = make_policy_fn(policy)
    trajectories: list[Trajectory] = []
    scores: list[int] = []
    for _ in range(batch_size):
        traj, score = run_episode(policy_fn, options=options)
        trajectories.append(traj)
        scores.append(score)
    return trajectories, scores


def _collect_parallel(
    policy: PolicyNetwork,
    batch_size: int,
    options: EpisodeOptions,
    num_workers: int,
) -> tuple[list[Trajectory], list[int]]:
    state_dict = {k: v.cpu() for k, v in policy.state_dict().items()}
    arch = _extract_architecture(policy)
    ctx = get_context("spawn")
    args = [options] * batch_size
    with ctx.Pool(
        processes=min(num_workers, batch_size),
        initializer=_init_episode_worker,
        initargs=(state_dict, *arch),
    ) as pool:
        results = pool.map(_run_episode_worker, args)
    return _unpack_results(results)


def _extract_architecture(policy: PolicyNetwork) -> tuple[int, int, int, int]:
    state_size = policy.trunk[0].in_features
    hidden1 = policy.trunk[0].out_features
    hidden2 = policy.trunk[2].out_features
    num_actions = policy.policy_head.out_features
    return state_size, hidden1, hidden2, num_actions


def _init_episode_worker(state_dict, state_size, hidden1, hidden2, num_actions):
    policy = PolicyNetwork(
        state_size=state_size, hidden1=hidden1,
        hidden2=hidden2, num_actions=num_actions,
    )
    policy.load_state_dict(state_dict)
    policy.eval()
    _WORKER_STATE["policy_fn"] = make_policy_fn(policy)


def _run_episode_worker(options: EpisodeOptions):
    return run_episode(_WORKER_STATE["policy_fn"], options=options)


def _unpack_results(
    results: list[tuple[Trajectory, int]],
) -> tuple[list[Trajectory], list[int]]:
    trajectories = [r[0] for r in results]
    scores = [r[1] for r in results]
    return trajectories, scores
