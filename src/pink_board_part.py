import logging

from src.actions.actions import ActionType
from src.pink_box import PinkBox
from src.dice import Dice, DiceColor


class PinkBoardPart:  # pylint: disable=too-few-public-methods
    def __init__(self) -> None:
        logging.debug("Initializing a pink board part")
        self.boxes: list[PinkBox] = [
            PinkBox(0, ActionType.NONE),
            PinkBox(0, ActionType.NONE),
            PinkBox(2, ActionType.REROLL),
            PinkBox(3, ActionType.REUSE),
            PinkBox(4, ActionType.PLUS_ONE),
            PinkBox(5, ActionType.GREEN_QUESTION_MARK),
            PinkBox(6, ActionType.YELLOW_QUESTION_MARK),
            PinkBox(2, ActionType.FOX),
            PinkBox(3, ActionType.GREY_QUESTION_MARK),
            PinkBox(4, ActionType.REROLL),
            PinkBox(5, ActionType.BLUE_QUESTION_MARK),
            PinkBox(6, ActionType.YELLOW_QUESTION_MARK),
        ]

    def add_dice(self, dice: Dice) -> ActionType:
        self._validate_dice(dice)
        logging.info(f'Adding dice {str(dice)} to pink board part')

        for index, pink_box in enumerate(self.boxes):
            if pink_box.value_used is None:
                pink_box.add_dice_value(dice.value)
                logging.info(f'Added dice {str(dice)} to pink box {index}')
                return pink_box.action if dice.value >= pink_box.action_filter_limit else ActionType.NONE

        raise ValueError("No free pink box available to add dice")

    @staticmethod
    def _validate_dice(dice: Dice) -> None:
        if dice.color not in [DiceColor.PINK, DiceColor.WHITE]:
            message = "Attempted to add a dice of a different color to pink board part"
            logging.warning(message)
            raise ValueError(message)

        if dice.value is None:
            message = "Attempted to add an unrolled dice to pink board part"
            logging.warning(message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        return sum(box.value_used for box in self.boxes if box.value_used is not None)
