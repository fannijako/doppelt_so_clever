from __future__ import annotations

from typing import TYPE_CHECKING

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.board.board_parts.blue_board_part import BlueBoardPart
from src.board.board_parts.grey_board_part import GreyBoardPart
from src.board.board_parts.pink_board_part import PinkBoardPart
from src.board.board_parts.green_board_part import GreenBoardPart
from src.board.board_parts.yellow_board_part import YellowBoardPart
from src.board.board_types import BoardDict

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
        self.consumed_immediate_actions = 0
        self.game_over = False

    _COLOR_INDEX = {c.value: i for i, c in enumerate(DiceColor)}
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

    _YELLOW_ROW_ACTIONS = {
        0: "blue_question_mark", 1: "reuse", 2: "yellow_question_mark",
        3: "green_question_mark", 4: "pink_question_mark",
    }
    _YELLOW_COL_ACTIONS = {
        0: "reroll", 1: "plus_one", 2: "grey_question_mark", 3: "fox",
    }
    _GREY_COL_ACTIONS = {
        1: "plus_one", 2: "yellow_question_mark", 3: "fox",
        4: "blue_question_mark", 5: "green_question_mark", 6: "pink_question_mark",
    }

    def to_dict(self) -> BoardDict:
        return {
            "blue": [
                {"value_used": box.value_used, "max_limit": box.maximum_value_limit, "action": box.action.value}
                for box in self.blue_board_part.boxes
            ],
            "green": [
                {"value_used": box.value_used, "multiplier": box.value_multiplier, "action": box.action.value}
                for box in self.green_board_part.boxes
            ],
            "pink": [
                {"value_used": box.value_used, "filter_limit": box.action_filter_limit, "action": box.action.value}
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
            "yellow_row_actions": {
                row: {
                    "action": action,
                    "available": row in self.yellow_board_part.available_rows_for_action,
                }
                for row, action in self._YELLOW_ROW_ACTIONS.items()
            },
            "yellow_col_actions": {
                col: {
                    "action": action,
                    "available": col in self.yellow_board_part.available_columns_for_action,
                }
                for col, action in self._YELLOW_COL_ACTIONS.items()
            },
            "grey": [
                {
                    "color": box.color.value,
                    "number": box.number,
                    "crossed": box.is_crossed,
                }
                for box in self.grey_board_part.boxes
            ],
            "grey_col_actions": {
                num: {
                    "action": action,
                    "available": num in self.grey_board_part.available_columns_for_action,
                }
                for num, action in self._GREY_COL_ACTIONS.items()
            },
            "foxes": self.foxes,
            "rerolls": {"gained": self.gained_rerolls, "usable": self.usable_rerolls},
            "reuses": {"gained": self.gained_reuses, "usable": self.usable_reuses},
            "plus_ones": {"gained": self.gained_plus_ones, "usable": self.usable_plus_ones},
        }

    STATE_SIZE = 372

    def to_tensor(self) -> list[float]:
        d = self.to_dict()
        return (
            self._filled_section_tensor(d["blue"], "value_used", 12.0, "max_limit", 12.0)
            + self._filled_section_tensor(d["green"], "value_used", 36.0, "multiplier", 6.0)
            + self._filled_section_tensor(d["pink"], "value_used", 6.0, "filter_limit", 6.0)
            + self._yellow_tensor(d)
            + self._grey_tensor(d)
            + self._action_flags_tensor(d)
            + self._resources_tensor(d)
        )

    @staticmethod
    def _filled_section_tensor(
        boxes: list[dict], value_key: str, value_max: float, attr_key: str, attr_max: float
    ) -> list[float]:
        t: list[float] = []
        for box in boxes:
            t.append((box[value_key] or 0) / value_max)
            t.append((box[attr_key] or 0) / attr_max)
            t.append(1.0 if box[value_key] is not None else 0.0)
        return t

    @staticmethod
    def _yellow_tensor(d: BoardDict) -> list[float]:
        t: list[float] = []
        for box in d["yellow"]:
            t.append(box["value"] / 6.0)
            t.append(box["row"] / 4.0)
            t.append(box["col"] / 3.0)
            t.append(1.0 if box["circled"] else 0.0)
            t.append(1.0 if box["crossed"] else 0.0)
        return t

    def _grey_tensor(self, d: BoardDict) -> list[float]:
        t: list[float] = []
        for box in d["grey"]:
            one_hot = [0.0] * len(DiceColor)
            one_hot[self._COLOR_INDEX[box["color"]]] = 1.0
            t.extend(one_hot)
            t.append(box["number"] / 6.0)
            t.append(1.0 if box["crossed"] else 0.0)
        return t

    def _action_flags_tensor(self, d: BoardDict) -> list[float]:
        t: list[float] = []
        for row in sorted(self._YELLOW_ROW_ACTIONS.keys()):
            t.append(1.0 if d["yellow_row_actions"][row]["available"] else 0.0)
        for col in sorted(self._YELLOW_COL_ACTIONS.keys()):
            t.append(1.0 if d["yellow_col_actions"][col]["available"] else 0.0)
        for num in sorted(self._GREY_COL_ACTIONS.keys()):
            t.append(1.0 if d["grey_col_actions"][num]["available"] else 0.0)
        return t

    @staticmethod
    def _resources_tensor(d: BoardDict) -> list[float]:
        return [
            d["foxes"] / 6.0,
            d["rerolls"]["gained"] / 6.0,
            d["rerolls"]["usable"] / 6.0,
            d["reuses"]["gained"] / 6.0,
            d["reuses"]["usable"] / 6.0,
            d["plus_ones"]["gained"] / 6.0,
            d["plus_ones"]["usable"] / 6.0,
        ]

    def evaluate(self) -> int:
        if not self.game_over:
            return 0
        return self._score_from_parts()

    def partial_evaluate(self) -> int:
        return self._score_from_parts()

    def _score_from_parts(self) -> int:
        part_values = [part.evaluate() for part in self._ordered_parts()]
        result = sum(part_values) + self.foxes * min(part_values)
        logger.info("Score", result)
        return result

    def min_section_score(self) -> int:
        return min(part.evaluate() for part in self._ordered_parts())

    def _ordered_parts(self) -> tuple:
        return (
            self.blue_board_part,
            self.pink_board_part,
            self.green_board_part,
            self.yellow_board_part,
            self.grey_board_part,
        )

    STRATEGIC_FEATURES_VERSION = 1
    STRATEGIC_FEATURES_SIZE = 16

    _SECTION_SCORE_MAXES = (78, 72, 92, 165, 88)
    _MIN_SECTION_SCORE_MAX = 72
    _FOX_COLUMN = 3

    def strategic_features(self) -> list[float]:
        scores = [part.evaluate() for part in self._ordered_parts()]
        return (
            self._normalized_section_scores(scores)
            + self._min_section_features(scores)
            + self._fox_distance_features()
        )

    def _normalized_section_scores(self, scores: list[int]) -> list[float]:
        return [score / maximum for score, maximum in zip(scores, self._SECTION_SCORE_MAXES)]

    def _min_section_features(self, scores: list[int]) -> list[float]:
        min_index = min(range(len(scores)), key=scores.__getitem__)
        one_hot = [1.0 if i == min_index else 0.0 for i in range(len(scores))]
        return [scores[min_index] / self._MIN_SECTION_SCORE_MAX] + one_hot

    def _fox_distance_features(self) -> list[float]:
        return [
            self._linear_fox_distance(self.blue_board_part.boxes),
            self._linear_fox_distance(self.pink_board_part.boxes),
            self._linear_fox_distance(self.green_board_part.boxes),
            self._column_fox_distance(
                self.yellow_board_part.available_columns_for_action,
                [box for box in self.yellow_board_part.boxes if box.column_position == self._FOX_COLUMN],
                lambda box: box.is_circled,
            ),
            self._column_fox_distance(
                self.grey_board_part.available_columns_for_action,
                [box for box in self.grey_board_part.boxes if box.number == self._FOX_COLUMN],
                lambda box: box.is_crossed,
            ),
        ]

    @staticmethod
    def _linear_fox_distance(boxes: list) -> float:
        fox_position = next(i for i, box in enumerate(boxes) if box.action == ActionType.FOX)
        filled = sum(1 for box in boxes if box.value_used is not None)
        boxes_to_reach = fox_position + 1
        return max(0, boxes_to_reach - filled) / boxes_to_reach

    def _column_fox_distance(self, available_columns: dict, column_boxes: list, is_marked) -> float:
        if self._FOX_COLUMN not in available_columns:
            return 0.0
        remaining = sum(1 for box in column_boxes if not is_marked(box))
        return remaining / len(column_boxes)
