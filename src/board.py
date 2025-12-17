import logging

from src.blue_board_part import BlueBoardPart
from src.pink_board_part import PinkBoardPart
from src.green_board_part import GreenBoardPart
from src.yellow_board_part import YellowBoardPart
from src.grey_board_part import GreyBoardPart


class Board:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.blue_board_part = BlueBoardPart()
        self.pink_board_part = PinkBoardPart()
        self.green_board_part = GreenBoardPart()
        self.yellow_board_part = YellowBoardPart()
        self.grey_board_part = GreyBoardPart()

    def evaluate(self) -> int:
        result = sum(
            board_part.evaluate()
            for board_part
            in (
                self.blue_board_part,
                self.pink_board_part,
                self.green_board_part,
                self.yellow_board_part,
                self.grey_board_part
            )
        )
        logging.info(f"Board evaluated to {result}")
        return result
