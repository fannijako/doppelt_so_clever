from typing import Optional

from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.not_immediate_actions.not_immediate_actions import NotImmediateActions
from src.actions.not_immediate_actions.fox_action import FoxAction


class ReRollAction(NotImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.REROLL)

    def save(self, board: Board) -> Optional[Action]:
        board.gained_rerolls += 1
        board.usable_rerolls += 1
        if board.gained_rerolls == 6:
            return FoxAction()
        return None

    def use(self, board: Board, automatic: bool) -> None:
        if board.usable_rerolls == 0:
            raise ValueError("No usable rerolls")
        board.usable_rerolls -= 1
