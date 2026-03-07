from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor

if TYPE_CHECKING:
    from src.board.board import Board


class PinkQuestionMarkAction(Action):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__(
            action_type=ActionType.PINK_QUESTION_MARK,
            is_immediate=True
        )

    def save(self) -> None:
        raise ValueError("Action cannot be saved")

    def use(self, board: Board, automatic: bool) -> list[Action]:
        pink_dice = Dice(DiceColor.PINK)
        pink_dice.set_value(6)
        action = board.pink_board_part.add_dice(pink_dice)
        return [action]
