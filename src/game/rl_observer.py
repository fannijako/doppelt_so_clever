from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from src.dice.dice_color import DiceColor
from src.game.game_observer import GameObserver
from src.actions.action_source import ActionSource

if TYPE_CHECKING:
    from src.dice.dice import Dice
    from src.board.board import Board
    from src.actions.base_action import Action


class DecisionType(Enum):
    CHOOSE_INDEX = "choose_index"
    CONFIRM = "confirm"
    CHOOSE_VALUE = "choose_value"


class PromptType(Enum):
    PICK_DIE_COLOR = 0
    PLACE_DIE = 1
    USE_REROLL = 2
    USE_REUSE = 3
    USE_PLUS_ONE = 4
    PICK_ACTION = 5
    PICK_PLACEMENT = 6
    PICK_DIE_INDEX = 7
    PICK_COLOR_SUBSTITUTE = 8
    PICK_COLOR_QUESTION_MARK = 9
    UNKNOWN = 10


_DICE_COLORS = list(DiceColor)
_MAX_OPTIONS = 30


@dataclass
class _ObserverState:
    round_number: int = 0
    subround: int = 0
    is_active: bool = True
    dice_values: dict[DiceColor, float] = field(
        default_factory=lambda: {c: 0.0 for c in DiceColor},
    )
    dice_available: dict[DiceColor, bool] = field(
        default_factory=lambda: {c: False for c in DiceColor},
    )


PROMPT_FEATURES_SIZE = len(PromptType)


class RLObserver(GameObserver):
    CONTEXT_SIZE = 19
    AUGMENTED_CONTEXT_SIZE = CONTEXT_SIZE + PROMPT_FEATURES_SIZE

    def __init__(self, board: Board, augmented: bool = False):
        self._board = board
        self._augmented = augmented
        self._state = _ObserverState()
        self._score: int | None = None
        self._failed_action_count = 0

    @property
    def score(self) -> int | None:
        return self._score

    @property
    def failed_action_count(self) -> int:
        return self._failed_action_count

    @property
    def board(self) -> Board:
        return self._board

    def on_round_started(self, round_number: int) -> None:
        self._state.round_number = round_number

    def on_round_completed(self, round_number: int) -> None:
        pass

    def on_active_round_started(self) -> None:
        self._state.is_active = True

    def on_passive_round_started(self) -> None:
        self._state.is_active = False

    def on_subround_started(self, subround: int) -> None:
        self._state.subround = subround

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        rolled_colors: set[DiceColor] = set()
        for die in dice:
            self._state.dice_values[die.color] = die.value / 6.0 if die.value is not None else 0.0
            rolled_colors.add(die.color)
        for color in DiceColor:
            self._state.dice_available[color] = color in rolled_colors

    def on_die_picked(self, die: Dice, discarded: list[Dice], available: list[Dice]) -> None:
        available_colors = {d.color for d in available}
        for color in DiceColor:
            self._state.dice_available[color] = color in available_colors

    def on_board_updated(self) -> None:
        pass

    def on_game_ended(self, score: int) -> None:
        self._score = score

    def on_action_executed(self, source: ActionSource, actions: list[Action]) -> None:
        if not actions:
            self._failed_action_count += 1

    def get_context_tensor(self, decision_type: DecisionType, num_options: int) -> list[float]:
        return (
            self._round_and_phase_features()
            + self._dice_value_features()
            + self._dice_availability_features()
            + _decision_type_one_hot(decision_type)
            + [num_options / _MAX_OPTIONS]
        )

    def get_state(
        self, decision_type: DecisionType, num_options: int, prompt: str = "",
    ) -> list[float]:
        ctx = self.get_context_tensor(decision_type, num_options)
        if self._augmented:
            ctx += _prompt_type_one_hot(classify_prompt(prompt))
        return self._board.to_tensor() + ctx

    @property
    def context_size(self) -> int:
        if self._augmented:
            return self.AUGMENTED_CONTEXT_SIZE
        return self.CONTEXT_SIZE

    def _round_and_phase_features(self) -> list[float]:
        return [
            self._state.round_number / 6.0,
            self._state.subround / 3.0,
            1.0 if self._state.is_active else 0.0,
        ]

    def _dice_value_features(self) -> list[float]:
        return [self._state.dice_values[c] for c in _DICE_COLORS]

    def _dice_availability_features(self) -> list[float]:
        return [1.0 if self._state.dice_available[c] else 0.0 for c in _DICE_COLORS]


def _decision_type_one_hot(decision_type: DecisionType) -> list[float]:
    return [
        1.0 if decision_type == DecisionType.CHOOSE_INDEX else 0.0,
        1.0 if decision_type == DecisionType.CONFIRM else 0.0,
        1.0 if decision_type == DecisionType.CHOOSE_VALUE else 0.0,
    ]


_PROMPT_PATTERNS: list[tuple[str, PromptType]] = [
    ("substitute", PromptType.PICK_COLOR_SUBSTITUTE),
    ("play white as", PromptType.PICK_COLOR_SUBSTITUTE),
    ("die color to reuse", PromptType.PICK_DIE_COLOR),
    ("Pick an available color", PromptType.PICK_DIE_COLOR),
    ("Place die", PromptType.PLACE_DIE),
    ("reroll", PromptType.USE_REROLL),
    ("reuse", PromptType.USE_REUSE),
    ("plus one", PromptType.USE_PLUS_ONE),
    ("action to use", PromptType.PICK_ACTION),
    ("placement", PromptType.PICK_PLACEMENT),
    ("die index", PromptType.PICK_DIE_INDEX),
    ("Pick an action index", PromptType.PICK_PLACEMENT),
    ("Enter index", PromptType.PICK_PLACEMENT),
    ("Enter a color", PromptType.PICK_COLOR_QUESTION_MARK),
]


def classify_prompt(prompt: str) -> PromptType:
    lower = prompt.lower()
    for pattern, prompt_type in _PROMPT_PATTERNS:
        if pattern.lower() in lower:
            return prompt_type
    return PromptType.UNKNOWN


def _prompt_type_one_hot(prompt_type: PromptType) -> list[float]:
    return [1.0 if pt == prompt_type else 0.0 for pt in PromptType]
