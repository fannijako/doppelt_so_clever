import logging
import random

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.actions.base_action import Action
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

    _SUBSTITUTABLE_COLORS = [DiceColor.BLUE, DiceColor.GREEN, DiceColor.PINK, DiceColor.YELLOW]
    _WHITE_SUBSTITUTABLE_COLORS = [*_SUBSTITUTABLE_COLORS, DiceColor.GREY]

    def place_white_dice(
        self,
        white_dice: Dice,
        automatic: bool,
        dice_by_color: dict[DiceColor, Dice],
        smaller_die: list[Dice] = None,
    ) -> list[Action]:
        if smaller_die is None:
            smaller_die = []
        if automatic:
            play_as = random.choice(self._WHITE_SUBSTITUTABLE_COLORS)
        else:
            play_as = DiceColor(input('Pick an available color to play white as: '))

        dispatch = {
            DiceColor.BLUE: lambda: self.blue_board_part.add_dice(
                dice_by_color[DiceColor.BLUE], white_dice
            ),
            DiceColor.GREEN: lambda: self.green_board_part.add_dice(white_dice),
            DiceColor.PINK: lambda: self.pink_board_part.add_dice(white_dice),
            DiceColor.YELLOW: lambda: self.yellow_board_part.place_dice(white_dice, automatic),
            DiceColor.GREY: lambda: self.grey_board_part.place_dice(white_dice, automatic, smaller_die),
        }
        result = dispatch[play_as]()
        return result if isinstance(result, list) else [result] if result else []

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
