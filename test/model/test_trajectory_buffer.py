import torch
import pytest

from model.trajectory_buffer import (
    Trajectory,
    Transition,
    compute_gae,
    build_batch,
)


def _make_trajectory(n: int, reward: float) -> Trajectory:
    traj = Trajectory()
    for i in range(n):
        traj.append(Transition(
            state=[0.0] * 10,
            action=0,
            log_prob=-0.5,
            value=float(i),
            action_mask=[1.0, 1.0, 0.0],
        ))
    traj.reward = reward
    return traj


class TestTrajectory:
    def test_length(self):
        traj = _make_trajectory(3, 10.0)
        assert len(traj) == 3

    def test_reward_stored(self):
        traj = _make_trajectory(3, 42.0)
        assert traj.reward == 42.0


class TestComputeGAE:
    def test_advantages_shape(self):
        traj = _make_trajectory(5, 100.0)
        advantages, _ = compute_gae(traj)
        assert advantages.shape == (5,)

    def test_returns_shape(self):
        traj = _make_trajectory(5, 100.0)
        _, returns = compute_gae(traj)
        assert returns.shape == (5,)

    def test_last_step_advantage_includes_reward(self):
        traj = _make_trajectory(1, 50.0)
        traj.transitions[0].value = 10.0
        advantages, _ = compute_gae(traj)
        assert advantages[0].item() == pytest.approx(40.0)

    def test_returns_equal_advantages_plus_values(self):
        traj = _make_trajectory(3, 20.0)
        advantages, returns = compute_gae(traj)
        values = torch.tensor([t.value for t in traj.transitions])
        assert torch.allclose(returns, advantages + values)


class TestBuildBatch:
    def test_batch_states_shape(self):
        batch = build_batch([_make_trajectory(3, 10.0), _make_trajectory(2, 20.0)])
        assert batch.states.shape == (5, 10)

    def test_batch_actions_dtype(self):
        batch = build_batch([_make_trajectory(3, 10.0)])
        assert batch.actions.dtype == torch.long

    def test_advantages_normalized_mean_near_zero(self):
        batch = build_batch([_make_trajectory(10, 50.0)])
        assert batch.advantages.mean().item() == pytest.approx(0.0, abs=1e-6)

    def test_states_length_matches_total_transitions(self):
        batch = build_batch([_make_trajectory(4, 10.0), _make_trajectory(6, 30.0)])
        assert batch.states.shape[0] == 10

    def test_actions_length_matches_total_transitions(self):
        batch = build_batch([_make_trajectory(4, 10.0), _make_trajectory(6, 30.0)])
        assert batch.actions.shape[0] == 10

    def test_returns_length_matches_total_transitions(self):
        batch = build_batch([_make_trajectory(4, 10.0), _make_trajectory(6, 30.0)])
        assert batch.returns.shape[0] == 10
