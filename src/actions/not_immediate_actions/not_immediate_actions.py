from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.board import Board


class NotImmediateActions(Action):
    def __init__(self, action_type: ActionType):
        super().__init__(action_type=action_type, is_immediate=False)

    def save(self) -> None:
        raise NotImplementedError

    def use(self, board: Board, automatic: bool) -> list[Action]:
        raise NotImplementedError
