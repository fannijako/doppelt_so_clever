import random

from model.rl_utils import EpisodeOptions, run_episode


def _random_policy(_state, action_mask):
    legal = [i for i, m in enumerate(action_mask) if m]
    return random.choice(legal), -0.5, 0.0


def test_non_zero_step_rewards_before_terminal():
    random.seed(0)
    trajectory, _score = run_episode(
        _random_policy,
        options=EpisodeOptions(augmented=False, max_rounds=2),
        training=True,
    )
    non_terminal_rewards = [t.reward for t in trajectory.transitions[:-1]]
    assert any(r != 0.0 for r in non_terminal_rewards)
