from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board import Board


class PlusOneAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.PLUS_ONE, is_immediate=False)

    def save(self):
        pass

    def use(self, board: Board) -> list[Action]:
        pass
