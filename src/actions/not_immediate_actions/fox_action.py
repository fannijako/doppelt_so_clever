from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board import Board


class FoxAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.FOX, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pass
