from __future__ import annotations

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


_DICE_COLORS = list(DiceColor)
_MAX_OPTIONS = 30


class RLObserver(GameObserver):
    CONTEXT_SIZE = 19

    def __init__(self, board: Board):
        self._board = board
        self._round_number = 0
        self._subround = 0
        self._is_active = True
        self._dice_values: dict[DiceColor, float] = {c: 0.0 for c in DiceColor}
        self._dice_available: dict[DiceColor, bool] = {c: False for c in DiceColor}
        self._score: int | None = None

    @property
    def score(self) -> int | None:
        return self._score

    def on_round_started(self, round_number: int) -> None:
        self._round_number = round_number

    def on_round_completed(self, round_number: int) -> None:
        pass

    def on_active_round_started(self) -> None:
        self._is_active = True

    def on_passive_round_started(self) -> None:
        self._is_active = False

    def on_subround_started(self, subround: int) -> None:
        self._subround = subround

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        rolled_colors: set[DiceColor] = set()
        for die in dice:
            self._dice_values[die.color] = die.value / 6.0 if die.value is not None else 0.0
            rolled_colors.add(die.color)
        for color in DiceColor:
            self._dice_available[color] = color in rolled_colors

    def on_die_picked(self, die: Dice, discarded: list[Dice], available: list[Dice]) -> None:
        available_colors = {d.color for d in available}
        for color in DiceColor:
            self._dice_available[color] = color in available_colors

    def on_board_updated(self) -> None:
        pass

    def on_game_ended(self, score: int) -> None:
        self._score = score

    def on_action_executed(self, source: ActionSource, actions: list[Action]) -> None:
        pass

    def get_context_tensor(self, decision_type: DecisionType, num_options: int) -> list[float]:
        return (
            self._round_and_phase_features()
            + self._dice_value_features()
            + self._dice_availability_features()
            + _decision_type_one_hot(decision_type)
            + [num_options / _MAX_OPTIONS]
        )

    def get_state(self, decision_type: DecisionType, num_options: int) -> list[float]:
        return self._board.to_tensor() + self.get_context_tensor(decision_type, num_options)

    def _round_and_phase_features(self) -> list[float]:
        return [
            self._round_number / 6.0,
            self._subround / 3.0,
            1.0 if self._is_active else 0.0,
        ]

    def _dice_value_features(self) -> list[float]:
        return [self._dice_values[c] for c in _DICE_COLORS]

    def _dice_availability_features(self) -> list[float]:
        return [1.0 if self._dice_available[c] else 0.0 for c in _DICE_COLORS]


def _decision_type_one_hot(decision_type: DecisionType) -> list[float]:
    return [
        1.0 if decision_type == DecisionType.CHOOSE_INDEX else 0.0,
        1.0 if decision_type == DecisionType.CONFIRM else 0.0,
        1.0 if decision_type == DecisionType.CHOOSE_VALUE else 0.0,
    ]
