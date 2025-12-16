import logging

from src.actions import Action
from src.pink_box import PinkBox


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
