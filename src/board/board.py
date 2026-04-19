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
            self.display()
            play_as = DiceColor(input('Pick an available color to play white as: '))

        dispatch = {
            DiceColor.BLUE: lambda: self.blue_board_part.add_dice(
                dice_by_color[DiceColor.BLUE], white_dice
            ),
            DiceColor.GREEN: lambda: self.green_board_part.add_dice(white_dice),
            DiceColor.PINK: lambda: self.pink_board_part.add_dice(white_dice),
            DiceColor.YELLOW: lambda: self.yellow_board_part.place_dice(white_dice, automatic, self),
            DiceColor.GREY: lambda: self.grey_board_part.place_dice(white_dice, automatic, smaller_die, self),
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

    def display(self) -> None:  # noqa: C901
        """Display the current state of the score sheet."""
        print("\n" + "=" * 60)
        print("                 SCORE SHEET")
        print("=" * 60)

        # Blue section
        print("\n[BLUE]  Values (max limit -> used): ", end="")
        for i, box in enumerate(self.blue_board_part.boxes):
            status = f"{box.value_used}" if box.value_used is not None else "_"
            limit = box.maximum_value_limit
            print(f"[{limit}>={status}]", end="")
            if i < len(self.blue_board_part.boxes) - 1:
                print(" ", end="")
        print()

        # Pink section
        print("\n[PINK]  Values (min required -> used): ", end="")
        for i, box in enumerate(self.pink_board_part.boxes):
            status = f"{box.value_used}" if box.value_used is not None else "_"
            limit = box.action_filter_limit
            print(f"[{limit}<={status}]", end="")
            if i < len(self.pink_board_part.boxes) - 1:
                print(" ", end="")
        print()

        # Green section
        print("\n[GREEN] Values (+/- alternates): ", end="")
        for i, box in enumerate(self.green_board_part.boxes):
            sign = "+" if box.index % 2 == 0 else "-"
            status = f"{sign}{box.value_used}" if box.value_used is not None else f"{sign}_"
            print(f"[{status}]", end="")
            if i < len(self.green_board_part.boxes) - 1:
                print(" ", end="")
        print()

        # Yellow section (5 rows x 4 columns grid)
        print("\n[YELLOW] Grid (rows 0-4, cols 0-3):")
        boxes_by_pos = {(b.row_position, b.column_position): b for b in self.yellow_board_part.boxes}
        for row in range(5):
            row_str = f"  Row {row}: "
            for col in range(4):
                box = boxes_by_pos.get((row, col))
                if box:
                    if box.is_crossed:
                        status = "X"
                    elif box.is_circled:
                        status = "o"
                    else:
                        status = str(box.value)
                    row_str += f"[{status:>2}] "
                else:
                    row_str += "[   ] "
            print(row_str)

        # Grey section (4 rows of dice values 1-6)
        print("\n[GREY]  Grid (Y/B/B/P colors x values 1-6):")
        for row_idx in range(4):
            row_boxes = self.grey_board_part.boxes[row_idx * 6:(row_idx + 1) * 6]
            colors = ["Y", "B", "B", "P"]
            row_str = f"  {colors[row_idx]}: "
            for box in row_boxes:
                status = "X" if box.is_crossed else str(box.number)
                row_str += f"[{status}] "
            print(row_str)

        # Resources
        print("\n[RESOURCES]")
        print(f"  Foxes: {self.foxes}")
        print(f"  Rerolls: {self.usable_rerolls} available")
        print(f"  Plus Ones: {self.usable_plus_ones} available")
        print(f"  Reuses: {self.usable_reuses} available")

        print("=" * 60 + "\n")
