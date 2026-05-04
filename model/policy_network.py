from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical

from src.board.board import Board
from src.game.rl_observer import RLObserver

STATE_SIZE = Board.STATE_SIZE + RLObserver.CONTEXT_SIZE
MAX_ACTIONS = 30


class PolicyNetwork(nn.Module):
    def __init__(
        self,
        state_size: int = STATE_SIZE,
        hidden1: int = 256,
        hidden2: int = 128,
        num_actions: int = MAX_ACTIONS,
    ):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(state_size, hidden1),
            nn.ReLU(),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
        )
        self.policy_head = nn.Linear(hidden2, num_actions)
        self.value_head = nn.Linear(hidden2, 1)

    def forward(self, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.trunk(state)
        logits = self.policy_head(features)
        value = self.value_head(features).squeeze(-1)
        return logits, value

    def get_action_and_value(
        self,
        state: torch.Tensor,
        action_mask: torch.Tensor,
        action: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, value = self(state)
        masked_logits = apply_action_mask(logits, action_mask)
        dist = Categorical(logits=masked_logits)
        if action is None:
            action = dist.sample()
        return action, dist.log_prob(action), dist.entropy(), value


def apply_action_mask(logits: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return logits + (1.0 - mask) * (-1e8)
