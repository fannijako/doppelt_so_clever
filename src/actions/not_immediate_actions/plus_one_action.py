import logging
import random
from typing import Optional

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.not_immediate_actions.not_immediate_actions import NotImmediateActions
from src.actions.immediate_actions.grey_question_mark import GreyQuestionMarkAction


class PlusOneAction(NotImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.PLUS_ONE)

    def save(self, board: Board) -> Optional[Action]:
        board.gained_plus_ones += 1
        board.usable_plus_ones += 1
        if board.gained_plus_ones == 6:
            return GreyQuestionMarkAction()
        return None

    def use(
        self,
        board: Board,
        automatic: bool,
        dice_by_color: dict[DiceColor, Dice] = None,
    ) -> Optional[Dice]:
        if board.usable_plus_ones == 0:
            raise ValueError("No usable plus ones")
        board.usable_plus_ones -= 1

        if dice_by_color is not None:
            usable_dice = [die for die in dice_by_color.values() if die.value is not None]
            if not usable_dice:
                return None

            if automatic:
                chosen_die = random.choice(usable_dice)
            else:
                logging.info(f"Available dice: {', '.join(str(die) for die in usable_dice)}")
                color = input('Pick a die color to reuse: ')
                chosen_die = dice_by_color[DiceColor(color)]

            logging.info(f"Plus one used with die: {chosen_die}")
            return chosen_die

        return None
