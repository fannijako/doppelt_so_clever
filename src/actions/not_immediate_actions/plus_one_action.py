from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_type import ActionType


class PlusOneAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.PLUS_ONE, is_immediate=False)

    def save(self, board: Board) -> None:
        return

    def use(self, board: Board, automatic: bool) -> list[Action]:
        return []
