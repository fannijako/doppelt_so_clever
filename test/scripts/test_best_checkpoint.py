import os
import tempfile
from unittest.mock import MagicMock, patch

import torch

from model.policy_network import PolicyNetwork
from model.ppo import PPOConfig, PPOTrainer
from scripts.train_rl import (
    EvalConfig,
    FeatureFlags,
    IOConfig,
    ModelConfig,
    TrainingConfig,
    TrainingContext,
    _maybe_eval_and_save_best,
)
from src.board.board import Board
from src.game.rl_observer import RLObserver


def _make_context(checkpoint_dir: str) -> tuple[TrainingContext, TrainingConfig]:
    config = TrainingConfig(
        features=FeatureFlags(augmented=True),
        io=IOConfig(checkpoint_dir=checkpoint_dir),
        eval=EvalConfig(interval=1, episodes=4),
        model=ModelConfig(hidden1=64, hidden2=32),
        batch_size=4,
    )
    state_size = Board.STATE_SIZE + RLObserver.AUGMENTED_CONTEXT_SIZE
    policy = PolicyNetwork(state_size=state_size, hidden1=64, hidden2=32)
    trainer = PPOTrainer(policy, PPOConfig())
    return TrainingContext(policy=policy, trainer=trainer), config


def _run_with_eval(
    tmpdir: str, eval_score: float,
    *, iteration: int = 0, best_eval_score: float = float("-inf"),
    interval: int = 1,
) -> float:
    ctx, config = _make_context(tmpdir)
    config.eval.interval = interval
    with patch("scripts.train_rl._evaluate_policy", return_value=eval_score):
        return _maybe_eval_and_save_best(
            ctx, config, iteration=iteration,
            best_eval_score=best_eval_score, writer=MagicMock(),
        )


def _load_best(tmpdir: str) -> dict:
    return torch.load(os.path.join(tmpdir, "best.pt"), weights_only=True)


def _best_path(tmpdir: str) -> str:
    return os.path.join(tmpdir, "best.pt")


class TestBestCheckpoint:
    def test_writes_best_pt_when_score_improves(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_with_eval(tmpdir, 200.0)
            assert os.path.exists(_best_path(tmpdir))

    def test_returns_new_best_score(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_with_eval(tmpdir, 180.0)
            assert result == 180.0

    def test_does_not_overwrite_when_score_lower(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_with_eval(tmpdir, 120.0, best_eval_score=200.0)
            assert result == 200.0

    def test_best_pt_not_written_when_score_lower(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_with_eval(tmpdir, 120.0, best_eval_score=200.0)
            assert not os.path.exists(_best_path(tmpdir))

    def test_skipped_when_interval_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_with_eval(tmpdir, 500.0, interval=0)
            assert not os.path.exists(_best_path(tmpdir))

    def test_best_checkpoint_contains_score(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_with_eval(tmpdir, 210.5, iteration=42)
            assert _load_best(tmpdir)["best_eval_score"] == 210.5

    def test_best_checkpoint_records_iteration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_with_eval(tmpdir, 210.5, iteration=42)
            assert _load_best(tmpdir)["best_eval_iteration"] == 42

    def test_best_checkpoint_records_augmented(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_with_eval(tmpdir, 210.5)
            assert _load_best(tmpdir)["augmented"] is True

    def test_best_checkpoint_records_state_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_with_eval(tmpdir, 210.5)
            assert "state_size" in _load_best(tmpdir)
