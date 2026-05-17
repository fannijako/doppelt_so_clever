import sys

import pytest

from model.early_stop import EarlyStopTracker
from model.policy_network import PolicyNetwork
from scripts import train_rl
from scripts.train_rl import (
    _build_config,
    _check_early_stop,
    _curriculum_rounds,
    _full_round_eval,
    _parse_arguments,
    FeatureFlags,
    IterationMetrics,
    TrainingConfig,
)


def _config(curriculum=False, iterations=5000, start=2, end=6):
    return TrainingConfig(
        iterations=iterations,
        features=FeatureFlags(
            curriculum=curriculum, max_rounds_start=start, max_rounds_end=end,
        ),
    )


def _parse(argv: list[str]):
    old = sys.argv
    sys.argv = ["train_rl.py"] + argv
    try:
        return _parse_arguments()
    finally:
        sys.argv = old


class TestCurriculumRoundsDisabled:
    def test_returns_none_when_disabled(self):
        assert _curriculum_rounds(0, _config(curriculum=False)) is None

    def test_returns_none_midway(self):
        assert _curriculum_rounds(50, _config(curriculum=False, iterations=100)) is None


class TestCurriculumRoundsEnabled:
    def test_first_iteration_returns_start(self):
        assert _curriculum_rounds(0, _config(curriculum=True, iterations=100)) == 2

    def test_last_iteration_returns_end(self):
        assert _curriculum_rounds(99, _config(curriculum=True, iterations=100)) == 6

    def test_midpoint_returns_intermediate(self):
        result = _curriculum_rounds(50, _config(curriculum=True, iterations=100))
        assert 2 <= result <= 6

    def test_single_iteration(self):
        assert _curriculum_rounds(0, _config(curriculum=True, iterations=1)) == 2


class TestCurriculumRequiresShapedRewards:
    def test_curriculum_with_no_shaped_rewards_raises(self):
        args = _parse(["--curriculum", "--no-shaped-rewards"])
        with pytest.raises(ValueError, match="curriculum requires shaped rewards"):
            _build_config(args)

    def test_curriculum_with_shaped_rewards_ok(self):
        args = _parse(["--curriculum"])
        config = _build_config(args)
        assert config.features.curriculum
        assert config.features.shaped_rewards

    def test_no_curriculum_no_shaping_ok(self):
        args = _parse(["--no-shaped-rewards"])
        config = _build_config(args)
        assert not config.features.shaped_rewards
        assert config.features.reward_config is not None


class TestEarlyStopUsesFullRoundEval:
    def test_curriculum_eval_uses_full_rounds(self, monkeypatch):
        captured = _capture_collect_batch(monkeypatch)
        config = TrainingConfig(features=FeatureFlags(curriculum=True))
        _full_round_eval(policy=None, config=config)
        assert captured["options"].max_rounds is None

    def test_curriculum_eval_uses_configured_episode_count(self, monkeypatch):
        captured = _capture_collect_batch(monkeypatch)
        config = TrainingConfig(features=FeatureFlags(curriculum=True))
        _full_round_eval(policy=None, config=config)
        assert captured["batch_size"] == config.features.curriculum_eval_episodes

    def test_curriculum_eval_returns_mean_score(self, monkeypatch):
        _capture_collect_batch(monkeypatch, score=180)
        config = TrainingConfig(features=FeatureFlags(curriculum=True))
        score = _full_round_eval(policy=None, config=config)
        assert score == pytest.approx(180.0)

    def test_no_curriculum_skips_full_round_eval(self, monkeypatch):
        called = _spy_full_round_eval(monkeypatch)
        config = TrainingConfig(features=FeatureFlags(curriculum=False))
        tracker = EarlyStopTracker(patience=5, smoothing=0.1)
        metrics = IterationMetrics(
            iteration=0, global_episode=1, scores=[200], elapsed=0.0,
        )
        policy = PolicyNetwork(state_size=391, hidden1=8, hidden2=8)
        _check_early_stop(tracker, metrics, policy, config)
        assert called["count"] == 0


def _capture_collect_batch(monkeypatch, score: int = 180) -> dict:
    captured: dict = {}

    def fake(_policy, batch_size, **kwargs):
        captured["batch_size"] = batch_size
        captured["options"] = kwargs.get("options")
        return [], [score] * batch_size

    monkeypatch.setattr(train_rl, "collect_batch", fake)
    return captured


def _spy_full_round_eval(monkeypatch) -> dict:
    called: dict = {"count": 0}

    def fake(_policy, _config):
        called["count"] += 1
        return 0.0

    monkeypatch.setattr(train_rl, "_full_round_eval", fake)
    return called
