from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.actions import Action, ActionType
from src.dice import Dice, DiceColor

if TYPE_CHECKING:
    from src.board import Board


class GreenQuestionMarkAction(Action):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__(
            action_type=ActionType.GREEN_QUESTION_MARK,
            is_immediate=True
        )

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        green_dice = Dice(DiceColor.GREEN)
        green_dice.set_value(6 if board.green_board_part.sign_of_next_empty_field() == 1 else 1)
        action = board.green_board_part.add_dice(green_dice)
        return [action]
