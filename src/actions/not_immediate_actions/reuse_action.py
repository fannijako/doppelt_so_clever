from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board import Board


class ReUseAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.REUSE, is_immediate=False)

    def save(self):
        pass

    def use(self, board: Board) -> list[Action]:
        pass
