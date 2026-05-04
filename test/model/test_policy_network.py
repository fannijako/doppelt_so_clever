import torch

from model.policy_network import STATE_SIZE, MAX_ACTIONS, apply_action_mask


class TestPolicyNetworkForward:
    def test_logits_shape(self, policy):
        state = torch.randn(1, STATE_SIZE)
        logits, _ = policy(state)
        assert logits.shape == (1, MAX_ACTIONS)

    def test_value_shape(self, policy):
        state = torch.randn(1, STATE_SIZE)
        _, value = policy(state)
        assert value.shape == (1,)

    def test_batch_logits_shape(self, policy):
        state = torch.randn(8, STATE_SIZE)
        logits, _ = policy(state)
        assert logits.shape == (8, MAX_ACTIONS)

    def test_batch_value_shape(self, policy):
        state = torch.randn(8, STATE_SIZE)
        _, value = policy(state)
        assert value.shape == (8,)


class TestGetActionAndValue:
    def test_action_within_mask(self, policy):
        state = torch.randn(1, STATE_SIZE)
        mask = torch.zeros(1, MAX_ACTIONS)
        mask[0, 2] = 1.0
        action, _, _, _ = policy.get_action_and_value(state, mask)
        assert action.item() == 2

    def test_log_prob_is_finite(self, policy):
        state = torch.randn(4, STATE_SIZE)
        mask = torch.ones(4, MAX_ACTIONS)
        _, log_prob, _, _ = policy.get_action_and_value(state, mask)
        assert torch.isfinite(log_prob).all()

    def test_entropy_is_non_negative(self, policy):
        state = torch.randn(4, STATE_SIZE)
        mask = torch.ones(4, MAX_ACTIONS)
        _, _, entropy, _ = policy.get_action_and_value(state, mask)
        assert (entropy >= 0).all()

    def test_provided_action_used(self, policy):
        state = torch.randn(1, STATE_SIZE)
        mask = torch.ones(1, MAX_ACTIONS)
        forced = torch.tensor([5])
        action, _, _, _ = policy.get_action_and_value(state, mask, forced)
        assert action.item() == 5


class TestApplyActionMask:
    def test_masked_logits_very_negative(self):
        logits = torch.zeros(1, 5)
        mask = torch.tensor([[1.0, 0.0, 1.0, 0.0, 0.0]])
        result = apply_action_mask(logits, mask)
        assert result[0, 1].item() < -1e7

    def test_valid_logits_unchanged(self):
        logits = torch.tensor([[1.0, 2.0, 3.0]])
        mask = torch.tensor([[1.0, 1.0, 1.0]])
        result = apply_action_mask(logits, mask)
        assert torch.equal(result, logits)
