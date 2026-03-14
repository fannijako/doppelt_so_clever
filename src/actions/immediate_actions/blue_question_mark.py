import logging

from src.dice.dice import Dice
from src.board.board import Board
from src.dice.dice_color import DiceColor
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.immediate_actions.immediate_actions import ImmediateActions


class BlueQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.BLUE_QUESTION_MARK)

    def use(self, board: Board, automatic: bool) -> list[Action]:
        value_limit_on_next_box = board.blue_board_part.get_value_limit_on_next_box()
        logging.debug(f"Value limit on next blue box: {value_limit_on_next_box}")

        blue_dice = Dice(DiceColor.BLUE)
        white_dice = Dice(DiceColor.WHITE)

        blue_dice.set_value(value_limit_on_next_box // 2)
        if value_limit_on_next_box % 2 == 0:
            white_dice.set_value(value_limit_on_next_box // 2)
        else:
            white_dice.set_value(value_limit_on_next_box // 2 + 1)

        logging.debug(f"Blue dice value set to: {blue_dice.value}")
        logging.debug(f"White dice value set to: {white_dice.value}")

        action = board.blue_board_part.add_dice(
            blue_dice,
            white_dice
        )
        return [action] if action else []
