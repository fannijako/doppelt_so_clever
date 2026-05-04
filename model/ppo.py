from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

from model.policy_network import PolicyNetwork
from model.trajectory_buffer import TrajectoryBatch


@dataclass
class PPOConfig:
    learning_rate: float = 3e-4
    clip_epsilon: float = 0.2
    epochs_per_batch: int = 4
    entropy_coefficient: float = 0.01
    value_loss_coefficient: float = 0.5
    max_grad_norm: float = 0.5
    minibatch_size: int = 256


@dataclass
class PPOUpdateResult:
    policy_loss: float
    value_loss: float
    entropy: float
    total_loss: float


class PPOTrainer:  # pylint: disable=too-few-public-methods
    def __init__(self, policy: PolicyNetwork, config: PPOConfig | None = None):
        self.policy = policy
        self.config = config or PPOConfig()
        self.optimizer = torch.optim.Adam(
            policy.parameters(), lr=self.config.learning_rate
        )

    def update(self, batch: TrajectoryBatch) -> PPOUpdateResult:
        results = [
            self._update_minibatch(mb, batch)
            for _ in range(self.config.epochs_per_batch)
            for mb in self._minibatches(batch)
        ]
        return self._average_results(results)

    @staticmethod
    def _average_results(results: list[PPOUpdateResult]) -> PPOUpdateResult:
        n = len(results)
        return PPOUpdateResult(
            policy_loss=sum(r.policy_loss for r in results) / n,
            value_loss=sum(r.value_loss for r in results) / n,
            entropy=sum(r.entropy for r in results) / n,
            total_loss=sum(r.total_loss for r in results) / n,
        )

    def _update_minibatch(
        self, indices: torch.Tensor, batch: TrajectoryBatch
    ) -> PPOUpdateResult:
        mb = self._slice_batch(indices, batch)
        _, new_log_probs, entropy, new_values = self.policy.get_action_and_value(
            mb["states"], mb["action_masks"], mb["actions"]
        )
        losses = self._compute_losses(mb, new_log_probs, entropy, new_values)
        self._optimize(losses["total_loss"])
        return PPOUpdateResult(**{k: v.item() for k, v in losses.items()})

    @staticmethod
    def _slice_batch(
        indices: torch.Tensor, batch: TrajectoryBatch
    ) -> dict[str, torch.Tensor]:
        return {
            "states": batch.states[indices],
            "actions": batch.actions[indices],
            "old_log_probs": batch.log_probs[indices],
            "advantages": batch.advantages[indices],
            "returns": batch.returns[indices],
            "action_masks": batch.action_masks[indices],
        }

    def _compute_losses(
        self,
        mb: dict[str, torch.Tensor],
        new_log_probs: torch.Tensor,
        entropy: torch.Tensor,
        new_values: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        policy_loss = self._clipped_surrogate_loss(
            new_log_probs, mb["old_log_probs"], mb["advantages"]
        )
        value_loss = nn.functional.mse_loss(new_values, mb["returns"])
        entropy_bonus = entropy.mean()
        total = (
            policy_loss
            + self.config.value_loss_coefficient * value_loss
            - self.config.entropy_coefficient * entropy_bonus
        )
        return {
            "policy_loss": policy_loss,
            "value_loss": value_loss,
            "entropy": entropy_bonus,
            "total_loss": total,
        }

    def _optimize(self, loss: torch.Tensor) -> None:
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy.parameters(), self.config.max_grad_norm)
        self.optimizer.step()

    def _clipped_surrogate_loss(
        self,
        new_log_probs: torch.Tensor,
        old_log_probs: torch.Tensor,
        advantages: torch.Tensor,
    ) -> torch.Tensor:
        ratio = torch.exp(new_log_probs - old_log_probs)
        clipped_ratio = torch.clamp(
            ratio,
            1.0 - self.config.clip_epsilon,
            1.0 + self.config.clip_epsilon,
        )
        return -torch.min(ratio * advantages, clipped_ratio * advantages).mean()

    def _minibatches(self, batch: TrajectoryBatch) -> list[torch.Tensor]:
        size = batch.states.shape[0]
        mb_size = min(self.config.minibatch_size, size)
        indices = torch.randperm(size)
        return [indices[i:i + mb_size] for i in range(0, size, mb_size)]
