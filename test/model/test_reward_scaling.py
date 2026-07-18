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
    def test_default_scale_is_one_over_10(self):
        assert DEFAULT_TERMINAL_REWARD_SCALE == pytest.approx(1.0 / 10.0)

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


def _hinge_options(threshold: float, lam: float) -> EpisodeOptions:
    return EpisodeOptions(
        augmented=False, max_rounds=2, terminal_reward_scale=1.0,
        tail_hinge_threshold=threshold, tail_hinge_lambda=lam,
    )


class TestTailHingeTerminalReward:
    def test_score_below_threshold_is_penalized(self):
        random.seed(3)
        trajectory, score = run_episode(_random_policy, options=_hinge_options(1000.0, 2.0))
        assert trajectory.reward == pytest.approx(float(score) + 2.0 * (float(score) - 1000.0))

    def test_score_above_threshold_unchanged(self):
        random.seed(4)
        trajectory, score = run_episode(_random_policy, options=_hinge_options(-1000.0, 2.0))
        assert trajectory.reward == pytest.approx(float(score))

    def test_zero_lambda_disables_hinge(self):
        random.seed(5)
        trajectory, score = run_episode(_random_policy, options=_hinge_options(1000.0, 0.0))
        assert trajectory.reward == pytest.approx(float(score))

    def test_hinge_composes_with_terminal_scale(self):
        random.seed(6)
        options = EpisodeOptions(
            augmented=False, max_rounds=2, terminal_reward_scale=0.1,
            tail_hinge_threshold=1000.0, tail_hinge_lambda=1.0,
        )
        trajectory, score = run_episode(_random_policy, options=options)
        assert trajectory.reward == pytest.approx((float(score) + (float(score) - 1000.0)) * 0.1)
