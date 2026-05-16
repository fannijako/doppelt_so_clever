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


class TestGAECombinedRewards:
    def test_single_step_combines_step_and_terminal_reward(self):
        traj = Trajectory(reward=100.0)
        traj.append(_make_transition(value=30.0, reward=5.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(75.0)

    def test_step_reward_propagates_to_earlier_steps(self):
        traj = Trajectory(reward=0.0)
        traj.append(_make_transition(value=0.0, reward=10.0))
        traj.append(_make_transition(value=0.0, reward=0.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(10.0)

    def test_terminal_reward_only_still_works(self):
        traj = Trajectory(reward=100.0)
        traj.append(_make_transition(value=0.0))
        traj.append(_make_transition(value=0.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(100.0)

    def test_zero_rewards_give_zero_advantages(self):
        traj = Trajectory(reward=0.0)
        traj.append(_make_transition(value=0.0))
        traj.append(_make_transition(value=0.0))
        advantages, _ = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert advantages[0].item() == pytest.approx(0.0)

    def test_returns_equal_advantages_plus_values(self):
        traj = Trajectory(reward=50.0)
        traj.append(_make_transition(value=2.0, reward=1.0))
        traj.append(_make_transition(value=3.0, reward=0.0))
        advantages, returns = compute_gae(traj, gamma=1.0, gae_lambda=1.0)
        assert returns[0].item() == pytest.approx(advantages[0].item() + 2.0)
