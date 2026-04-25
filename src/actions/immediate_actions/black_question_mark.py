from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.immediate_actions.immediate_actions import ImmediateActions
from src.actions.immediate_actions.blue_question_mark import BlueQuestionMarkAction
from src.actions.immediate_actions.grey_question_mark import GreyQuestionMarkAction
from src.actions.immediate_actions.pink_question_mark import PinkQuestionMarkAction
from src.actions.immediate_actions.green_question_mark import GreenQuestionMarkAction
from src.actions.immediate_actions.yellow_question_mark import YellowQuestionMarkAction

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler

_COLOR_ACTION_MAP = {
    "blue": BlueQuestionMarkAction,
    "green": GreenQuestionMarkAction,
    "grey": GreyQuestionMarkAction,
    "pink": PinkQuestionMarkAction,
    "yellow": YellowQuestionMarkAction,
}


class BlackQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.BLACK_QUESTION_MARK)

    def use(self, board: Board, input_handler: InputHandler) -> list[Action]:
        action_to_use = self._pick_action(input_handler=input_handler)
        return action_to_use().use(board, input_handler)

    def _pick_action(self, input_handler: InputHandler) -> type[Action]:
        color = input_handler.choose_value(
            'Enter a color: ',
            list(_COLOR_ACTION_MAP.keys()),
        )
        if color not in _COLOR_ACTION_MAP:
            raise ValueError("Invalid color")
        return _COLOR_ACTION_MAP[color]
