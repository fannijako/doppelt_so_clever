import logging

from enum import Enum

from src.actions.action_type import ActionType
from src.board.boxes.yellow_box import YellowBox
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor


class YellowBoardAction(Enum):
    CIRCLE = "circle"
    CROSS = "cross"


class YellowBoardPart:
    def __init__(self) -> None:
        logging.debug("Initializing a yellow board part")
        self.boxes: list[YellowBox] = [
            YellowBox(
                value=3,
                row_position=0,
                column_position=1,
            ),
            YellowBox(
                value=6,
                row_position=0,
                column_position=3,
            ),
            YellowBox(
                value=1,
                row_position=1,
                column_position=0,
            ),
            YellowBox(
                value=2,
                row_position=1,
                column_position=2,
            ),
            YellowBox(
                value=4,
                row_position=2,
                column_position=1,
            ),
            YellowBox(
                value=3,
                row_position=2,
                column_position=3,
            ),
            YellowBox(
                value=2,
                row_position=3,
                column_position=0,
            ),
            YellowBox(
                value=5,
                row_position=3,
                column_position=2,
            ),
            YellowBox(
                value=5,
                row_position=4,
                column_position=1,
            ),
            YellowBox(
                value=4,
                row_position=4,
                column_position=3,
            ),
        ]

        self._available_columns_for_action = {
            0: ActionType.REROLL,
            1: ActionType.PLUS_ONE,
            2: ActionType.GREY_QUESTION_MARK,
            3: ActionType.FOX,
        }

        self._available_rows_for_action = {
            0: ActionType.BLUE_QUESTION_MARK,
            1: ActionType.REUSE,
            2: ActionType.YELLOW_QUESTION_MARK,
            3: ActionType.GREEN_QUESTION_MARK,
            4: ActionType.PINK_QUESTION_MARK,
        }

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

    def add_dice(self, dice: Dice, row_position: int, column_position: int, action: YellowBoardAction) -> ActionType:
        if (row_position, column_position, action) not in self.possible_dice_placements(dice):
            raise ValueError("Invalid dice placement")

        if action == YellowBoardAction.CIRCLE:
            self.circle_box(dice.value, row_position, column_position)
        elif action == YellowBoardAction.CROSS:
            self.cross_box(dice.value, row_position, column_position)

        return self._calculate_actions_received_in_round()

    def possible_dice_placements(self, dice: Dice) -> list[tuple[int, int, YellowBoardAction]]:
        return [
            (
                box.row_position,
                box.column_position,
                YellowBoardAction.CIRCLE
            )
            for box in self.boxes
            if box.value == dice.value and not box.is_circled
        ] + [
            (
                box.row_position,
                box.column_position,
                YellowBoardAction.CROSS
            )
            for box in self.boxes
            if box.value == dice.value and box.is_circled and not box.is_crossed
        ]

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

    def _calculate_actions_received_in_round(self) -> list[ActionType]:
        return self._calculate_row_actions_received_in_round() + self._calculate_column_actions_received_in_round()

    def _calculate_row_actions_received_in_round(self) -> list[ActionType]:
        actions = []
        for row_position in range(5):
            circled_boxes_in_row = [
                box.is_circled for box in self.boxes
                if box.row_position == row_position
            ]
            is_row_eligible_for_action = len(circled_boxes_in_row) == sum(circled_boxes_in_row)
            is_action_already_used = row_position not in self._available_rows_for_action
            if is_row_eligible_for_action and not is_action_already_used:
                actions.append(self._available_rows_for_action[row_position])
                self._available_rows_for_action.pop(row_position)

        return actions

    def _calculate_column_actions_received_in_round(self) -> list[ActionType]:
        actions = []
        for column_position in range(4):
            circled_boxes_in_column = [
                box.is_circled for box in self.boxes
                if box.column_position == column_position
            ]
            is_column_eligible_for_action = len(circled_boxes_in_column) == sum(circled_boxes_in_column)
            is_action_already_used = column_position not in self._available_columns_for_action
            if is_column_eligible_for_action and not is_action_already_used:
                actions.append(self._available_columns_for_action[column_position])
                self._available_columns_for_action.pop(column_position)

        return actions

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
