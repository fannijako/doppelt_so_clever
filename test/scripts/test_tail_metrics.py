from unittest.mock import patch

from model.policy_network import PolicyNetwork
from model.ppo import PPOConfig, PPOTrainer
from scripts.evaluate_rl import BaselineResult
from scripts.train_rl import (
    EvalConfig,
    FeatureFlags,
    ModelConfig,
    TrainingConfig,
    _eval_metric,
    _evaluate_policy,
)
from src.board.board import Board
from src.game.rl_observer import RLObserver


class TestEvalMetric:
    def test_mean_metric(self):
        assert _eval_metric([100, 200], "mean") == 150.0

    def test_p10_metric_picks_low_quantile(self):
        assert _eval_metric(list(range(1, 101)), "p10") == 11.0


class TestEvaluatePolicyBestMetric:
    def test_p10_best_metric_drives_evaluation(self):
        config = TrainingConfig(
            features=FeatureFlags(augmented=True),
            eval=EvalConfig(interval=1, episodes=4, best_metric="p10"),
            model=ModelConfig(hidden1=64, hidden2=32),
            batch_size=4,
        )
        state_size = Board.STATE_SIZE + RLObserver.AUGMENTED_CONTEXT_SIZE
        policy = PolicyNetwork(state_size=state_size, hidden1=64, hidden2=32)
        PPOTrainer(policy, PPOConfig())
        with patch("scripts.train_rl.collect_batch", return_value=([], list(range(1, 101)))):
            assert _evaluate_policy(policy, config) == 11.0


class TestBaselineTailMetrics:
    def test_percentile_p10(self):
        result = BaselineResult(name="x", scores=list(range(1, 101)))
        assert result.percentile(10) == 11.0

    def test_percentile_p1(self):
        result = BaselineResult(name="x", scores=list(range(1, 101)))
        assert result.percentile(1) == 2.0

    def test_pct_below_threshold(self):
        result = BaselineResult(name="x", scores=[100, 150, 139, 141])
        assert result.pct_below(140) == 50.0

    def test_pct_below_zero_when_all_above(self):
        result = BaselineResult(name="x", scores=[150, 160])
        assert result.pct_below(140) == 0.0
