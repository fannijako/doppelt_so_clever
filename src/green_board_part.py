import logging

from src.actions import Action
from src.green_box import GreenBox
from src.dice import Dice, DiceColor


class GreenBoardPart:
    def __init__(self) -> None:
        logging.debug("Initializing a green board part")
        self.boxes: list[GreenBox] = [
            GreenBox(2, Action.NONE),
            GreenBox(2, Action.REROLL),
            GreenBox(2, Action.NONE),
            GreenBox(1, Action.BLUE_QUESTION_MARK),
            GreenBox(3, Action.REUSE),
            GreenBox(3, Action.NONE),
            GreenBox(3, Action.FOX),
            GreenBox(2, Action.GREY_QUESTION_MARK),
            GreenBox(3, Action.PLUS_ONE),
            GreenBox(1, Action.NONE),
            GreenBox(4, Action.PINK_QUESTION_MARK),
            GreenBox(1, Action.YELLOW_QUESTION_MARK),
        ]

    def add_dice(self, dice: Dice) -> Action:
        self._validate_dice(dice)
        logging.info(f'Adding dice {str(dice)} to green board part')
        for index, green_box in enumerate(self.boxes):
            if green_box.value_used is None:
                green_box.add_dice_value(dice.value)
                logging.info(f'Added dice {str(dice)} to green box {index}: {green_box.value_used}')
                return green_box.action

        raise ValueError("No free green box available to add dice")

    @staticmethod
    def _validate_dice(dice: Dice) -> None:
        if dice.color not in [DiceColor.GREEN, DiceColor.WHITE]:
            message = "Attempted to add a dice of a different color to green board part"
            logging.warning(message)
            raise ValueError(message)

        if dice.value is None:
            message = "Attempted to add an unrolled dice to green board part"
            logging.warning(message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        used_boxes = [box for box in self.boxes if box.value_used is not None]

        if len(used_boxes) % 2 != 0:
            used_boxes.pop()

        return sum(
            box.value_used if index % 2 == 0 else -box.value_used
            for index, box in enumerate(used_boxes)
        )
