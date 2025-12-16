import logging

from src.actions import Action
from src.green_box import GreenBox
from src.die import Die, DieColor


class GreenBoardPart:
    def __init__(self) -> None:
        logging.debug("Initializing a green board part")
        self.boxes: list[GreenBox] = [
            GreenBox(0, Action.NONE),
            GreenBox(0, Action.REROLL),
            GreenBox(2, Action.NONE),
            GreenBox(3, Action.BLUE_QUESTION_MARK),
            GreenBox(4, Action.REUSE),
            GreenBox(5, Action.NONE),
            GreenBox(6, Action.FOX),
            GreenBox(2, Action.GREY_QUESTION_MARK),
            GreenBox(3, Action.PLUS_ONE),
            GreenBox(4, Action.NONE),
            GreenBox(5, Action.PINK_QUESTION_MARK),
            GreenBox(6, Action.YELLOW_QUESTION_MARK),
        ]

    def add_die(self, die: Die) -> Action:
        self._validate_die(die)
        logging.info(f'Adding die {str(die)} to green board part')
        for index, green_box in enumerate(self.boxes):
            if green_box.value_used is None:
                green_box.add_die_value(die.value)
                logging.info(f'Added die {str(die)} to green box {index}: {green_box.value_used}')
                return green_box.action

        raise ValueError("No free green box available to add die")

    @staticmethod
    def _validate_die(die: Die) -> None:
        if die.color not in [DieColor.GREEN, DieColor.WHITE]:
            message = "Attempted to add a die of a different color to green board part"
            logging.warning(message)
            raise ValueError(message)

        if die.value is None:
            message = "Attempted to add an unrolled die to green board part"
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
