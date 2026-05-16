from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from src.input_handler.base_input_handler import InputHandler
from src.game.rl_observer import RLObserver, DecisionType, _MAX_OPTIONS
from src.game.reward_shaper import BoardSnapshot, RewardConfig, RewardShaper


@dataclass
class Transition:
    state: list[float]
    action: int
    log_prob: float
    value: float
    action_mask: list[bool]
    reward: float = 0.0


class Policy(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(
        self, state: list[float], action_mask: list[bool]
    ) -> tuple[int, float, float]: ...


class RLInputHandler(InputHandler):
    def __init__(
        self,
        observer: RLObserver,
        policy: Policy,
        training: bool = True,
        reward_config: RewardConfig | None = None,
    ):
        self._observer = observer
        self._policy = policy
        self._training = training
        self._trajectory: list[Transition] = []
        self._shaper = RewardShaper(reward_config)
        self._last_snapshot: BoardSnapshot | None = None

    @property
    def trajectory(self) -> list[Transition]:
        return list(self._trajectory)

    def choose_index(self, prompt: str, options: list[Any]) -> int:
        return self._decide(DecisionType.CHOOSE_INDEX, len(options), prompt)

    def confirm(self, prompt: str) -> bool:
        return self._decide(DecisionType.CONFIRM, 2, prompt) == 0

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        return valid_values[self._decide(DecisionType.CHOOSE_VALUE, len(valid_values), prompt)]

    def clear_trajectory(self) -> None:
        self._trajectory.clear()
        self._last_snapshot = None

    def flush_terminal_step_reward(self) -> None:
        if not self._training or not self._trajectory or self._last_snapshot is None:
            return
        current = self._capture_snapshot()
        self._trajectory[-1].reward += self._shaper.compute(self._last_snapshot, current)
        self._last_snapshot = current

    def _decide(self, decision_type: DecisionType, num_options: int, prompt: str = "") -> int:
        if self._training:
            self._attribute_pending_reward()
        state = self._observer.get_state(decision_type, num_options, prompt)
        mask = _build_action_mask(num_options)
        action, log_prob, value = self._policy(state, mask)
        if self._training:
            self._trajectory.append(
                Transition(
                    state=state, action=action, log_prob=log_prob,
                    value=value, action_mask=mask,
                )
            )
        return action

    def _attribute_pending_reward(self) -> None:
        current = self._capture_snapshot()
        if self._last_snapshot is not None and self._trajectory:
            self._trajectory[-1].reward += self._shaper.compute(self._last_snapshot, current)
        self._last_snapshot = current

    def _capture_snapshot(self) -> BoardSnapshot:
        return BoardSnapshot.capture(
            self._observer.board, self._observer, self._shaper.config,
        )


def _build_action_mask(num_options: int) -> list[bool]:
    return [i < num_options for i in range(_MAX_OPTIONS)]
