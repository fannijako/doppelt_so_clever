import logging

from src.actions import Action
from src.pink_box import PinkBox
from src.die import Die, DieColor


class PinkBoardPart:  # pylint: disable=too-few-public-methods
    def __init__(self) -> None:
        logging.debug("Initializing a pink board part")
        self.boxes: list[PinkBox] = [
            PinkBox(0, Action.NONE),
            PinkBox(0, Action.NONE),
            PinkBox(2, Action.REROLL),
            PinkBox(3, Action.REUSE),
            PinkBox(4, Action.PLUS_ONE),
            PinkBox(5, Action.GREEN_QUESTION_MARK),
            PinkBox(6, Action.YELLOW_QUESTION_MARK),
            PinkBox(2, Action.FOX),
            PinkBox(3, Action.GREY_QUESTION_MARK),
            PinkBox(4, Action.REROLL),
            PinkBox(5, Action.BLUE_QUESTION_MARK),
            PinkBox(6, Action.YELLOW_QUESTION_MARK),
        ]

    def add_die(self, die: Die) -> Action:
        self._validate_die(die)
        logging.info(f'Adding die {str(die)} to pink board part')

        for index, pink_box in enumerate(self.boxes):
            if pink_box.value_used is None:
                pink_box.add_die_value(die.value)
                logging.info(f'Added die {str(die)} to pink box {index}')
                return pink_box.action if die.value >= pink_box.action_filter_limit else Action.NONE

        raise ValueError("No free pink box available to add die")

    @staticmethod
    def _validate_die(die: Die) -> None:
        if die.color != DieColor.PINK:
            message = "Attempted to add a die of a different color to pink board part"
            logging.warning(message)
            raise ValueError(message)

        if die.value is None:
            message = "Attempted to add an unrolled die to pink board part"
            logging.warning(message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])
