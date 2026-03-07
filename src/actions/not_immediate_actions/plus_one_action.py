from typing import Optional

from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.not_immediate_actions.not_immediate_actions import NotImmediateActions
from src.actions.immediate_actions.grey_question_mark import GreyQuestionMarkAction


class PlusOneAction(NotImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.PLUS_ONE)

    def save(self, board: Board) -> Optional[Action]:
        board.gained_plus_ones += 1
        if board.gained_plus_ones == 6:
            return GreyQuestionMarkAction()
        return None

    def use(self, board: Board, automatic: bool) -> None:
        if board.usable_plus_ones == 0:
            raise ValueError("No usable plus ones")
        board.usable_plus_ones -= 1
