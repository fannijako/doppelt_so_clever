import pytest
import torch

from model.policy_network import PolicyNetwork, STATE_SIZE, MAX_ACTIONS
from model.trajectory_buffer import Trajectory, Transition, build_batch
from model.ppo import PPOTrainer, PPOConfig


def _make_policy():
    torch.manual_seed(42)
    return PolicyNetwork()


def _make_state():
    return [0.5] * STATE_SIZE


def _make_action_mask():
    mask = [0.0] * MAX_ACTIONS
    mask[0] = 1.0
    mask[1] = 1.0
    mask[2] = 1.0
    return mask


def _make_trajectory():
    traj = Trajectory()
    for i in range(5):
        traj.append(Transition(
            state=_make_state(),
            action=i % 3,
            log_prob=-1.0,
            value=float(i),
            action_mask=_make_action_mask(),
        ))
    traj.reward = 100.0
    return traj


@pytest.fixture()
def policy():
    return _make_policy()


@pytest.fixture()
def dummy_batch():
    traj = _make_trajectory()
    return build_batch([traj, traj])


@pytest.fixture()
def trainer():
    config = PPOConfig(epochs_per_batch=2, minibatch_size=4)
    return PPOTrainer(_make_policy(), config)
