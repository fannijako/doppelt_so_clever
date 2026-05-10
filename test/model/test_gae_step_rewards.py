import pytest

from model.trajectory_buffer import Trajectory, Transition, compute_gae


def _make_transition(value: float) -> Transition:
    return Transition(
        state=[0.0] * 10,
        action=0,
        log_prob=-0.5,
        value=value,
        action_mask=[1.0, 1.0, 0.0],
    )


class TestGAETerminalRewardOnly:
    def test_single_step_advantage_is_terminal_minus_value(self):
        traj = Trajectory(reward=100.0)
        traj.append(_make_transition(value=30.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(70.0)

    def test_terminal_reward_propagates_to_earlier_steps(self):
        traj = Trajectory(reward=100.0)
        traj.append(_make_transition(value=0.0))
        traj.append(_make_transition(value=0.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(100.0)

    def test_no_discounting_with_gamma_one(self):
        traj = Trajectory(reward=50.0)
        traj.append(_make_transition(value=0.0))
        traj.append(_make_transition(value=0.0))
        traj.append(_make_transition(value=0.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(50.0)

    def test_zero_terminal_reward_gives_zero_advantages(self):
        traj = Trajectory(reward=0.0)
        traj.append(_make_transition(value=0.0))
        traj.append(_make_transition(value=0.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(0.0)

    def test_returns_equal_terminal_reward_for_zero_values(self):
        traj = Trajectory(reward=80.0)
        traj.append(_make_transition(value=0.0))
        _, returns = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert returns[0].item() == pytest.approx(80.0)
