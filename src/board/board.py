import logging

from src.board.board_parts.blue_board_part import BlueBoardPart
from src.board.board_parts.pink_board_part import PinkBoardPart
from src.board.board_parts.green_board_part import GreenBoardPart
from src.board.board_parts.yellow_board_part import YellowBoardPart
from src.board.board_parts.grey_board_part import GreyBoardPart


class Board:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        self.blue_board_part = BlueBoardPart()
        self.pink_board_part = PinkBoardPart()
        self.green_board_part = GreenBoardPart()
        self.yellow_board_part = YellowBoardPart()
        self.grey_board_part = GreyBoardPart()
        self.foxes = 0
        self.gained_rerolls = 0
        self.usable_rerolls = 0
        self.gained_plus_ones = 0
        self.usable_plus_ones = 0
        self.gained_reuses = 0
        self.usable_reuses = 0

    def evaluate(self) -> int:
        part_values = [
            board_part.evaluate()
            for board_part
            in (
                self.blue_board_part,
                self.pink_board_part,
                self.green_board_part,
                self.yellow_board_part,
                self.grey_board_part
            )
        ]
        result = sum(part_values) + self.foxes * min(part_values)
        logging.info(f"Board evaluated to {result}")
        return result
