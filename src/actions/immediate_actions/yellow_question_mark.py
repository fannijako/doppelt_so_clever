from __future__ import annotations

from typing import TYPE_CHECKING

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.board.board_parts.yellow_board_part import YellowBoardAction
from src.actions.immediate_actions.immediate_actions import ImmediateActions

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler

logger = GameLogger(__name__)


class YellowQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(
            action_type=ActionType.YELLOW_QUESTION_MARK,
        )

    def use(self, board: Board, input_handler: InputHandler) -> list[Action]:
        yellow_dice = Dice(DiceColor.YELLOW)
        possible_placements = board.yellow_board_part.all_possible_dice_placements(yellow_dice)
        (
            selected_value,
            selected_row,
            selected_column,
            selected_action
        ) = self._pick_placement(possible_placements, input_handler)

        yellow_dice.set_value(selected_value)

        try:
            return board.yellow_board_part.add_dice(
                dice=yellow_dice,
                row_position=selected_row,
                column_position=selected_column,
                action=selected_action
            )
        except ValueError:
            return []

    def _pick_placement(
        self,
        possible_placements: list[tuple[int, int, int, YellowBoardAction]],
        input_handler: InputHandler,
    ) -> tuple[int, int, int, YellowBoardAction]:
        index = input_handler.choose_index("Select a placement: ", possible_placements)
        return possible_placements[index]
