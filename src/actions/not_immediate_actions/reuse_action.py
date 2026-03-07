from typing import Optional

from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.not_immediate_actions.not_immediate_actions import NotImmediateActions
from src.actions.immediate_actions.pink_question_mark import PinkQuestionMarkAction


class ReUseAction(NotImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.REUSE)

    def save(self, board: Board) -> Optional[Action]:
        board.gained_reuses += 1
        if board.gained_reuses == 6:
            return PinkQuestionMarkAction()
        return None

    def use(self, board: Board, automatic: bool) -> None:
        if board.usable_reuses == 0:
            raise ValueError("No usable reuses")
        board.usable_reuses -= 1
