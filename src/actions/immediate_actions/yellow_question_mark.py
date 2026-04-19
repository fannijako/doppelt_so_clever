import random
import logging

from src.dice.dice import Dice
from src.board.board import Board
from src.dice.dice_color import DiceColor
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.board.board_parts.yellow_board_part import YellowBoardAction
from src.actions.immediate_actions.immediate_actions import ImmediateActions


class YellowQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(
            action_type=ActionType.YELLOW_QUESTION_MARK,
        )

    def use(self, board: Board, automatic: bool) -> list[Action]:
        yellow_dice = Dice(DiceColor.YELLOW)
        possible_placements = board.yellow_board_part.all_possible_dice_placements(yellow_dice)
        (
            selected_value,
            selected_row,
            selected_column,
            selected_action
        ) = self._pick_placement(possible_placements, automatic)

        yellow_dice.set_value(selected_value)

        return board.yellow_board_part.add_dice(
            dice=yellow_dice,
            row_position=selected_row,
            column_position=selected_column,
            action=selected_action
        )

    def _pick_placement(
        self,
        possible_placements: list[tuple[int, int, int, YellowBoardAction]],
        automatic: bool
    ) -> tuple[int, int, int, YellowBoardAction]:
        if automatic:
            return random.choice(possible_placements)

        logging.info(f"Possible placements: {possible_placements}")
        options = [
            f"val={val} row={row} col={col} {'circle' if act.value == 'circle' else 'cross'}"
            for val, row, col, act in possible_placements
        ]
        if self.pick_option_callback:
            index = self.pick_option_callback("Pick a yellow placement", options)  # pylint: disable=not-callable
        else:
            index = int(input("Select a placement: "))
        return possible_placements[index]
