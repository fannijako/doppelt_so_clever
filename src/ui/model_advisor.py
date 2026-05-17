from __future__ import annotations

from pathlib import Path

import torch

from src.game.rl_observer import RLObserver, DecisionType, _MAX_OPTIONS

from model.policy_network import PolicyNetwork, apply_action_mask
from scripts.train_rl import require_phase3_metadata


_DEFAULT_CHECKPOINT = Path(__file__).resolve().parents[2] / "model" / "checkpoints" / "best.pt"


class ModelAdvisor:  # pylint: disable=too-few-public-methods
    def __init__(self, observer: RLObserver, checkpoint_path: Path | None = None):
        self._observer = observer
        self._policy, self._augmented = self._load_policy(
            checkpoint_path or _DEFAULT_CHECKPOINT,
        )

    @staticmethod
    def read_augmented_from_checkpoint(checkpoint_path: Path | None = None) -> bool:
        path = checkpoint_path or _DEFAULT_CHECKPOINT
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        require_phase3_metadata(checkpoint, str(path))
        return checkpoint["augmented"]

    @property
    def augmented(self) -> bool:
        return self._augmented

    def get_recommendation(
        self, num_options: int, prompt: str, options: list | None = None,
    ) -> int | None:
        if num_options < 1:
            return None
        state = self._observer.get_state(
            self._infer_decision_type(num_options, prompt),
            num_options, prompt, options,
        )
        mask = [i < num_options for i in range(_MAX_OPTIONS)]
        return self._predict(state, mask)

    @staticmethod
    def _infer_decision_type(num_options: int, prompt: str) -> DecisionType:
        lower = prompt.lower()
        if num_options == 2 and any(word in lower for word in ("confirm", "reroll", "reuse", "plus one")):
            return DecisionType.CONFIRM
        if any(word in lower for word in ("color", "substitute")):
            return DecisionType.CHOOSE_VALUE
        return DecisionType.CHOOSE_INDEX

    @torch.no_grad()
    def _predict(self, state: list[float], action_mask: list[bool]) -> int:
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        mask_t = torch.tensor([float(m) for m in action_mask], dtype=torch.float32).unsqueeze(0)
        logits, _ = self._policy(state_t)
        masked_logits = apply_action_mask(logits, mask_t)
        return int(masked_logits.argmax(dim=-1).item())

    @staticmethod
    def _load_policy(checkpoint_path: Path) -> tuple[PolicyNetwork, bool]:
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        require_phase3_metadata(checkpoint, str(checkpoint_path))
        policy = PolicyNetwork(
            state_size=checkpoint["state_size"],
            hidden1=checkpoint.get("hidden1", 256),
            hidden2=checkpoint.get("hidden2", 128),
        )
        policy.load_state_dict(checkpoint["policy_state_dict"])
        policy.eval()
        return policy, checkpoint["augmented"]
