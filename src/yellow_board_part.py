import logging

from src.actions import Action
from src.yellow_box import YellowBox
from src.dice import Dice, DiceColor


class YellowBoardPart:  # pylint: disable=too-few-public-methods
    def __init__(self) -> None:
        logging.debug("Initializing a yellow board part")
        self.boxes: list[YellowBox] = [
            YellowBox(
                value=3,
                row_position=0,
                column_position=1,
                row_action=Action.BLUE_QUESTION_MARK,
                column_action=Action.PLUS_ONE
            ),
            YellowBox(
                value=6,
                row_position=0,
                column_position=3,
                row_action=Action.BLUE_QUESTION_MARK,
                column_action=Action.FOX
            ),
            YellowBox(
                value=1,
                row_position=1,
                column_position=0,
                row_action=Action.REUSE,
                column_action=Action.REROLL
            ),
            YellowBox(
                value=2,
                row_position=1,
                column_position=2,
                row_action=Action.REUSE,
                column_action=Action.GREEN_QUESTION_MARK
            ),
            YellowBox(
                value=4,
                row_position=2,
                column_position=1,
                row_action=Action.YELLOW_QUESTION_MARK,
                column_action=Action.PLUS_ONE
            ),
            YellowBox(
                value=3,
                row_position=2,
                column_position=3,
                row_action=Action.YELLOW_QUESTION_MARK,
                column_action=Action.FOX
            ),
            YellowBox(
                value=2,
                row_position=3,
                column_position=0,
                row_action=Action.GREEN_QUESTION_MARK,
                column_action=Action.REROLL
            ),
            YellowBox(
                value=5,
                row_position=3,
                column_position=2,
                row_action=Action.GREEN_QUESTION_MARK,
                column_action=Action.GREEN_QUESTION_MARK
            ),
            YellowBox(
                value=5,
                row_position=4,
                column_position=1,
                row_action=Action.PINK_QUESTION_MARK,
                column_action=Action.PLUS_ONE
            ),
            YellowBox(
                value=4,
                row_position=4,
                column_position=3,
                row_action=Action.PINK_QUESTION_MARK,
                column_action=Action.FOX
            ),
        ]

    def circle_box(self, value: int, row_position: int, column_position: int) -> None:
        for box in self.boxes:
            if box.value == value and box.row_position == row_position and box.column_position == column_position:
                box.circle_box()
                return
        raise ValueError("Box not found")

    def cross_box(self, value: int, row_position: int, column_position: int) -> None:
        for box in self.boxes:
            if box.value == value and box.row_position == row_position and box.column_position == column_position:
                box.cross_box()
                return
        raise ValueError("Box not found")

    @staticmethod
    def _validate_dice(dice: Dice) -> None:
        if dice.color not in [DiceColor.YELLOW, DiceColor.WHITE]:
            message = "Attempted to add a dice of a different color to yellow board part"
            logging.warning(message)
            raise ValueError(message)

        if dice.value is None:
            message = "Attempted to add an unrolled dice to yellow board part"
            logging.warning(message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        point_dice_number_map = {
            0: 0,
            1: 3,
            2: 10,
            3: 21,
            4: 36,
            5: 55,
            6: 75,
            7: 96,
            8: 118,
            9: 141,
            10: 165,
        }
        number_of_boxes_used = len([box for box in self.boxes if box.is_crossed])
        return point_dice_number_map.get(number_of_boxes_used, 0)
