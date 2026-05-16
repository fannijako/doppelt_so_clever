import os
import tempfile

import pytest
import torch

from model.policy_network import PolicyNetwork
from model.ppo import PPOConfig, PPOTrainer
from scripts.train_rl import (
    FeatureFlags,
    IOConfig,
    TrainingConfig,
    _save_checkpoint,
)
from scripts.evaluate_rl import _load_policy as evaluate_load
from scripts.monte_carlo import _load_policy as monte_carlo_load
from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.ui.model_advisor import ModelAdvisor


def _make_checkpoint(tmpdir: str, augmented: bool) -> str:
    config = TrainingConfig(
        features=FeatureFlags(augmented=augmented),
        io=IOConfig(checkpoint_dir=tmpdir),
        hidden1=64, hidden2=32,
    )
    state_size = Board.STATE_SIZE + (
        RLObserver.AUGMENTED_CONTEXT_SIZE if augmented else RLObserver.CONTEXT_SIZE
    )
    policy = PolicyNetwork(state_size=state_size, hidden1=64, hidden2=32)
    trainer = PPOTrainer(policy, PPOConfig())
    _save_checkpoint(policy, trainer, iteration=0, config=config)
    return os.path.join(tmpdir, "checkpoint_000000.pt")


class TestCheckpointMetadata:
    def test_save_includes_state_size_and_augmented(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True)
            ckpt = torch.load(path, weights_only=True)
            assert "state_size" in ckpt
            assert "augmented" in ckpt
            assert ckpt["augmented"] is True

    def test_save_records_non_augmented(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=False)
            ckpt = torch.load(path, weights_only=True)
            assert ckpt["augmented"] is False
            assert ckpt["state_size"] == Board.STATE_SIZE + RLObserver.CONTEXT_SIZE


class TestLoaderRoundTrip:
    def test_evaluate_loader_returns_augmented(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True)
            _, augmented = evaluate_load(path)
            assert augmented is True

    def test_evaluate_loader_state_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True)
            policy, _ = evaluate_load(path)
            assert policy.trunk[0].in_features == Board.STATE_SIZE + RLObserver.AUGMENTED_CONTEXT_SIZE

    def test_monte_carlo_loader_returns_non_augmented(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=False)
            _, augmented = monte_carlo_load(path)
            assert augmented is False

    def test_monte_carlo_loader_legacy_state_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=False)
            policy, _ = monte_carlo_load(path)
            assert policy.trunk[0].in_features == Board.STATE_SIZE + RLObserver.CONTEXT_SIZE

    def test_advisor_reads_augmented_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True)
            assert ModelAdvisor.read_augmented_from_checkpoint(path) is True

    def test_loading_legacy_checkpoint_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "legacy.pt")
            policy = PolicyNetwork(state_size=Board.STATE_SIZE + RLObserver.CONTEXT_SIZE)
            torch.save({"policy_state_dict": policy.state_dict()}, path)
            with pytest.raises(ValueError, match="Phase 3 metadata"):
                evaluate_load(path)
