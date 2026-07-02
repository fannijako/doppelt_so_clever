import os
import tempfile

import pytest
import torch

from model.policy_network import PolicyNetwork
from model.ppo import PPOConfig, PPOTrainer
from scripts.train_rl import (
    FeatureFlags,
    IOConfig,
    ModelConfig,
    TrainingConfig,
    _compute_state_size,
    _save_checkpoint,
    assert_observer_state_size,
)
from scripts.evaluate_rl import _load_policy as evaluate_load
from scripts.monte_carlo import _load_policy as monte_carlo_load
from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.ui.model_advisor import ModelAdvisor


def _make_checkpoint(tmpdir: str, augmented: bool, strategic_features: bool = False) -> str:
    config = TrainingConfig(
        features=FeatureFlags(augmented=augmented, strategic_features=strategic_features),
        io=IOConfig(checkpoint_dir=tmpdir),
        model=ModelConfig(hidden1=64, hidden2=32),
    )
    state_size = _compute_state_size(augmented, strategic_features)
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

    def test_save_records_default_reward_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True)
            assert torch.load(path, weights_only=True)["reward_mode"] == "none"


class TestLoaderRoundTrip:
    def test_evaluate_loader_returns_augmented(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True)
            _, augmented, _ = evaluate_load(path)
            assert augmented is True

    def test_evaluate_loader_state_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True)
            policy, _, _ = evaluate_load(path)
            assert policy.trunk[0].in_features == Board.STATE_SIZE + RLObserver.AUGMENTED_CONTEXT_SIZE

    def test_monte_carlo_loader_returns_non_augmented(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=False)
            _, augmented, _ = monte_carlo_load(path)
            assert augmented is False

    def test_monte_carlo_loader_legacy_state_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=False)
            policy, _, _ = monte_carlo_load(path)
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


class TestStrategicFeaturesMetadata:
    def test_save_records_strategic_features(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True, strategic_features=True)
            assert torch.load(path, weights_only=True)["strategic_features"] is True

    def test_save_records_strategic_features_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True, strategic_features=True)
            ckpt = torch.load(path, weights_only=True)
            assert ckpt["strategic_features_version"] == Board.STRATEGIC_FEATURES_VERSION

    def test_save_records_strategic_state_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True, strategic_features=True)
            ckpt = torch.load(path, weights_only=True)
            assert ckpt["state_size"] == (
                Board.STATE_SIZE + RLObserver.AUGMENTED_CONTEXT_SIZE + Board.STRATEGIC_FEATURES_SIZE
            )

    def test_loader_returns_strategic_features(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True, strategic_features=True)
            _, _, strategic_features = evaluate_load(path)
            assert strategic_features is True

    def test_pre_strategic_checkpoint_defaults_to_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _make_checkpoint(tmpdir, augmented=True, strategic_features=False)
            _, _, strategic_features = evaluate_load(path)
            assert strategic_features is False


class TestObserverCheckpointParity:
    def test_observer_missing_strategic_features_raises(self):
        observer = RLObserver(Board(), augmented=True, strategic_features=False)
        expected = _compute_state_size(augmented=True, strategic_features=True)
        with pytest.raises(ValueError, match="does not match"):
            assert_observer_state_size(observer, expected)

    def test_observer_with_unexpected_strategic_features_raises(self):
        observer = RLObserver(Board(), augmented=True, strategic_features=True)
        expected = _compute_state_size(augmented=True, strategic_features=False)
        with pytest.raises(ValueError, match="does not match"):
            assert_observer_state_size(observer, expected)

    def test_matching_observer_passes(self):
        observer = RLObserver(Board(), augmented=True, strategic_features=True)
        expected = _compute_state_size(augmented=True, strategic_features=True)
        assert assert_observer_state_size(observer, expected) is None
