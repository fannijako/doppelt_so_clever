from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.not_immediate_actions.not_immediate_actions import NotImmediateActions


class FoxAction(NotImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.FOX)

    def save(self, board: Board) -> None:
        board.foxes += 1

    def use(self, board: Board, automatic: bool) -> list[Action]:
        raise ValueError("Action cannot be used")
