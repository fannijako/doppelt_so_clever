from __future__ import annotations

import torch

from model.policy_network import PolicyNetwork
from model.trajectory_buffer import Trajectory, Transition as BufferTransition
from src.actions.action_handler import ActionHandler
from src.board.board import Board
from src.game.game import Game
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler, Transition


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
        ))
    return traj


def run_episode(
    policy_fn,
    augmented: bool = False,
    max_rounds: int | None = None,
    training: bool = True,
) -> tuple[Trajectory, int]:
    board = Board()
    observer = RLObserver(board, augmented=augmented)
    handler = RLInputHandler(observer, policy_fn, training=training)
    game = Game(
        input_handler=handler,
        board=board,
        observer=observer,
        action_handler=ActionHandler(board=board),
    )
    score = game.play(max_rounds=max_rounds)
    return convert_trajectory(handler.trajectory, float(score)), score


def collect_batch(
    policy: PolicyNetwork,
    batch_size: int,
    augmented: bool = False,
    max_rounds: int | None = None,
) -> tuple[list[Trajectory], list[int]]:
    policy_fn = make_policy_fn(policy)
    trajectories: list[Trajectory] = []
    scores: list[int] = []
    for _ in range(batch_size):
        traj, score = run_episode(policy_fn, augmented=augmented, max_rounds=max_rounds)
        trajectories.append(traj)
        scores.append(score)
    return trajectories, scores
