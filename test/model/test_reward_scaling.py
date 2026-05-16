import random

import pytest

from model.rl_utils import DEFAULT_TERMINAL_REWARD_SCALE, EpisodeOptions, run_episode


def _random_policy(_state, action_mask):
    legal = [i for i, m in enumerate(action_mask) if m]
    return random.choice(legal), -0.5, 0.0


def _options(scale: float) -> EpisodeOptions:
    return EpisodeOptions(
        augmented=False, max_rounds=2, terminal_reward_scale=scale,
    )


class TestTerminalRewardScale:
    def test_default_scale_is_one_over_300(self):
        assert DEFAULT_TERMINAL_REWARD_SCALE == pytest.approx(1.0 / 300.0)

    def test_terminal_reward_scaled_by_factor(self):
        random.seed(0)
        trajectory, score = run_episode(
            _random_policy, options=_options(1.0 / 100.0),
        )
        assert trajectory.reward == pytest.approx(float(score) / 100.0)

    def test_scale_of_one_preserves_raw_score(self):
        random.seed(1)
        trajectory, score = run_episode(_random_policy, options=_options(1.0))
        assert trajectory.reward == pytest.approx(float(score))

    def test_zero_scale_zeros_terminal_reward(self):
        random.seed(2)
        trajectory, _score = run_episode(_random_policy, options=_options(0.0))
        assert trajectory.reward == 0.0
