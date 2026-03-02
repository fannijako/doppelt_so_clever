from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.actions import Action, ActionType
from src.dice import Dice, DiceColor

if TYPE_CHECKING:
    from src.board import Board


class PinkQuestionMarkAction(Action):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__(action_type=ActionType.PINK_QUESTION_MARK, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pink_dice = Dice(DiceColor.PINK)
        pink_dice.set_value(6)
        action = board.pink_board_part.add_dice(pink_dice)
        return [action]
