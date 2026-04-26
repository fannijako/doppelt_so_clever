from __future__ import annotations

from typing import TYPE_CHECKING

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger
from src.actions.base_action import Action
from src.board.board_parts.blue_board_part import BlueBoardPart
from src.board.board_parts.grey_board_part import GreyBoardPart
from src.board.board_parts.pink_board_part import PinkBoardPart
from src.board.board_parts.green_board_part import GreenBoardPart
from src.board.board_parts.yellow_board_part import YellowBoardPart

if TYPE_CHECKING:
    from src.input_handler import InputHandler

logger = GameLogger(__name__)


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
        input_handler: InputHandler,
        dice_by_color: dict[DiceColor, Dice],
        smaller_die: list[Dice] = None,
    ) -> list[Action]:
        if smaller_die is None:
            smaller_die = []
        color_value = input_handler.choose_value(
            'Pick an available color to play white as: ',
            [str(c.value) for c in self._WHITE_SUBSTITUTABLE_COLORS],
        )
        play_as = DiceColor(color_value)

        dispatch = {
            DiceColor.BLUE: lambda: self.blue_board_part.add_dice(
                dice_by_color[DiceColor.BLUE], white_dice
            ),
            DiceColor.GREEN: lambda: self.green_board_part.add_dice(white_dice),
            DiceColor.PINK: lambda: self.pink_board_part.add_dice(white_dice),
            DiceColor.YELLOW: lambda: self.yellow_board_part.place_dice(white_dice, input_handler),
            DiceColor.GREY: lambda: self.grey_board_part.place_dice(white_dice, input_handler, smaller_die),
        }
        result = dispatch[play_as]()
        return result if isinstance(result, list) else [result] if result else []

    def to_dict(self) -> dict:
        return {
            "blue": [
                {"value_used": box.value_used, "max_limit": box.maximum_value_limit}
                for box in self.blue_board_part.boxes
            ],
            "green": [
                {"value_used": box.value_used, "multiplier": box.value_multiplier}
                for box in self.green_board_part.boxes
            ],
            "pink": [
                {"value_used": box.value_used, "filter_limit": box.action_filter_limit}
                for box in self.pink_board_part.boxes
            ],
            "yellow": [
                {
                    "value": box.value,
                    "row": box.row_position,
                    "col": box.column_position,
                    "circled": box.is_circled,
                    "crossed": box.is_crossed,
                }
                for box in self.yellow_board_part.boxes
            ],
            "grey": [
                {
                    "color": box.color.value,
                    "number": box.number,
                    "crossed": box.is_crossed,
                }
                for box in self.grey_board_part.boxes
            ],
            "foxes": self.foxes,
            "rerolls": {"gained": self.gained_rerolls, "usable": self.usable_rerolls},
            "reuses": {"gained": self.gained_reuses, "usable": self.usable_reuses},
            "plus_ones": {"gained": self.gained_plus_ones, "usable": self.usable_plus_ones},
        }

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
        logger.info("Score", result)
        return result
