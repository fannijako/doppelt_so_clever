import pytest

from model.trajectory_buffer import Trajectory, Transition, compute_gae


def _make_transition(value: float, reward: float = 0.0) -> Transition:
    return Transition(
        state=[0.0] * 10,
        action=0,
        log_prob=-0.5,
        value=value,
        action_mask=[1.0, 1.0, 0.0],
        reward=reward,
    )


class TestGAEWithStepRewards:
    def test_step_reward_included_in_advantage(self):
        traj = Trajectory(reward=0.0)
        traj.append(_make_transition(value=0.0, reward=5.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(5.0)

    def test_terminal_and_step_reward_combined(self):
        traj = Trajectory(reward=100.0)
        traj.append(_make_transition(value=0.0, reward=10.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(110.0)

    def test_step_reward_zero_by_default(self):
        traj = Trajectory(reward=50.0)
        traj.append(_make_transition(value=10.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(40.0)

    def test_intermediate_step_does_not_get_terminal(self):
        traj = Trajectory(reward=100.0)
        traj.append(_make_transition(value=0.0, reward=5.0))
        traj.append(_make_transition(value=0.0, reward=0.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[1].item() == pytest.approx(100.0)

    def test_returns_include_step_rewards(self):
        traj = Trajectory(reward=0.0)
        traj.append(_make_transition(value=2.0, reward=8.0))
        _, returns = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert returns[0].item() == pytest.approx(8.0)
