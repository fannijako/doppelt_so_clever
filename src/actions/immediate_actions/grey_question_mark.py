import random
import logging

from src.dice.dice import Dice
from src.board.board import Board

logger = logging.getLogger(__name__)
from src.dice.dice_color import DiceColor
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.immediate_actions.immediate_actions import ImmediateActions


class GreyQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.GREY_QUESTION_MARK)

    def use(self, board: Board, automatic: bool) -> list[Action]:
        dice = Dice(DiceColor.GREY)
        color, value = self._pick_color_and_value(board, automatic)
        dice.set_value(value)

        return board.grey_board_part.add_dice(
            dice=dice,
            smaller_die=[],
            color_to_use_grey_as=color,
        )

    def _pick_color_and_value(self, board: Board, automatic: bool) -> tuple[DiceColor, int]:
        possible_combinations = [
            (box.color, box.number)
            for box in board.grey_board_part.boxes
            if not box.is_crossed
        ]
        if automatic:
            return random.choice(possible_combinations)

        logger.info(f"Possible combinations: {possible_combinations}")
        index = int(input("Enter index: "))
        return possible_combinations[index]
