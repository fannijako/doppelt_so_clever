from __future__ import annotations

from dataclasses import dataclass, field

import torch


@dataclass
class Transition:
    state: list[float]
    action: int
    log_prob: float
    value: float
    action_mask: list[float]


@dataclass
class Trajectory:
    transitions: list[Transition] = field(default_factory=list)
    reward: float = 0.0

    def append(self, transition: Transition) -> None:
        self.transitions.append(transition)

    def __len__(self) -> int:
        return len(self.transitions)


@dataclass
class TrajectoryBatch:
    states: torch.Tensor
    actions: torch.Tensor
    log_probs: torch.Tensor
    values: torch.Tensor
    action_masks: torch.Tensor
    advantages: torch.Tensor
    returns: torch.Tensor


def compute_gae(
    trajectory: Trajectory,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
) -> tuple[torch.Tensor, torch.Tensor]:
    n = len(trajectory)
    advantages = torch.zeros(n)
    values = torch.tensor([t.value for t in trajectory.transitions])
    terminal_reward = trajectory.reward

    last_gae = 0.0
    for t in reversed(range(n)):
        next_value = values[t + 1] if t + 1 < n else 0.0
        is_last = 1.0 if t == n - 1 else 0.0
        reward = terminal_reward * is_last
        delta = reward + gamma * next_value - values[t]
        last_gae = delta + gamma * gae_lambda * (1.0 - is_last) * last_gae
        advantages[t] = last_gae

    returns = advantages + values
    return advantages, returns


def build_batch(trajectories: list[Trajectory]) -> TrajectoryBatch:
    flat = _flatten_trajectories(trajectories)
    return TrajectoryBatch(
        states=torch.tensor(flat["states"]),
        actions=torch.tensor(flat["actions"], dtype=torch.long),
        log_probs=torch.tensor(flat["log_probs"]),
        values=torch.tensor(flat["values"]),
        action_masks=torch.tensor(flat["action_masks"]),
        advantages=_normalize(torch.tensor(flat["advantages"])),
        returns=torch.tensor(flat["returns"]),
    )


def _flatten_trajectories(trajectories: list[Trajectory]) -> dict[str, list]:
    flat: dict[str, list] = {
        "states": [], "actions": [], "log_probs": [],
        "values": [], "action_masks": [], "advantages": [], "returns": [],
    }
    for traj in trajectories:
        _append_trajectory(traj, flat)
    return flat


def _append_trajectory(traj: Trajectory, flat: dict[str, list]) -> None:
    advantages, returns = compute_gae(traj)
    for i, t in enumerate(traj.transitions):
        flat["states"].append(t.state)
        flat["actions"].append(t.action)
        flat["log_probs"].append(t.log_prob)
        flat["values"].append(t.value)
        flat["action_masks"].append(t.action_mask)
        flat["advantages"].append(advantages[i].item())
        flat["returns"].append(returns[i].item())


def _normalize(tensor: torch.Tensor) -> torch.Tensor:
    if tensor.std() < 1e-8:
        return tensor - tensor.mean()
    return (tensor - tensor.mean()) / (tensor.std() + 1e-8)
