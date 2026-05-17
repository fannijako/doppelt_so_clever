import torch
import pytest

from model.ppo import PPOConfig, PPOUpdateResult


class TestPPOUpdateResult:
    def test_returns_result_object(self, trainer, dummy_batch):
        result = trainer.update(dummy_batch)
        assert isinstance(result, PPOUpdateResult)

    def test_policy_loss_is_finite(self, trainer, dummy_batch):
        result = trainer.update(dummy_batch)
        assert torch.isfinite(torch.tensor(result.policy_loss))

    def test_value_loss_is_finite(self, trainer, dummy_batch):
        result = trainer.update(dummy_batch)
        assert torch.isfinite(torch.tensor(result.value_loss))

    def test_entropy_is_non_negative(self, trainer, dummy_batch):
        result = trainer.update(dummy_batch)
        assert result.entropy >= 0.0

    def test_total_loss_is_finite(self, trainer, dummy_batch):
        result = trainer.update(dummy_batch)
        assert torch.isfinite(torch.tensor(result.total_loss))


class TestPPOWeightUpdate:
    def test_weights_change_after_update(self, trainer, dummy_batch):
        old_params = [p.clone() for p in trainer.policy.parameters()]
        trainer.update(dummy_batch)
        new_params = list(trainer.policy.parameters())
        changed = any(
            not torch.equal(old, new)
            for old, new in zip(old_params, new_params)
        )
        assert changed

    def test_multiple_updates_reduce_value_loss(self, trainer, dummy_batch):
        first = trainer.update(dummy_batch)
        for _ in range(5):
            result = trainer.update(dummy_batch)
        assert result.value_loss < first.value_loss


class TestPPOConfig:
    def test_default_clip_epsilon(self):
        config = PPOConfig()
        assert config.clip_epsilon == pytest.approx(0.2)

    def test_default_learning_rate(self):
        config = PPOConfig()
        assert config.learning_rate == pytest.approx(3e-4)

    def test_default_gamma(self):
        config = PPOConfig()
        assert config.gamma == pytest.approx(1.0)

    def test_default_gae_lambda(self):
        config = PPOConfig()
        assert config.gae_lambda == pytest.approx(0.95)
