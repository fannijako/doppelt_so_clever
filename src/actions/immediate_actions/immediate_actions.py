from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_type import ActionType


class ImmediateActions(Action):
    def __init__(self, action_type: ActionType):
        super().__init__(
            action_type=action_type,
            is_immediate=True
        )

    def save(self, board: Board) -> None:
        raise ValueError("Action cannot be saved")

    def use(self, board: Board, automatic: bool) -> list[Action]:
        raise NotImplementedError
