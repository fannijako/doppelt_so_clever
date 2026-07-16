from __future__ import annotations

from typing import TYPE_CHECKING

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.immediate_actions.immediate_actions import ImmediateActions

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler

logger = GameLogger(__name__)


class GreyQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.GREY_QUESTION_MARK)

    def use(self, board: Board, input_handler: InputHandler) -> list[Action]:
        possible_combinations = self._possible_combinations(board)
        if not possible_combinations:
            return []

        dice = Dice(DiceColor.GREY)
        color, value = self._pick_color_and_value(possible_combinations, input_handler)
        dice.set_value(value)

        try:
            return board.grey_board_part.add_dice(
                dice=dice,
                smaller_die=[],
                color_to_use_grey_as=color,
            )
        except ValueError:
            return []

    @staticmethod
    def _possible_combinations(board: Board) -> list[tuple[DiceColor, int]]:
        return [
            (box.color, box.number)
            for box in board.grey_board_part.boxes
            if not box.is_crossed
        ]

    @staticmethod
    def _pick_color_and_value(
        possible_combinations: list[tuple[DiceColor, int]],
        input_handler: InputHandler,
    ) -> tuple[DiceColor, int]:
        index = input_handler.choose_index("Enter index: ", possible_combinations)
        return possible_combinations[index]
