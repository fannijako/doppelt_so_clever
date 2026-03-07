from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board import Board


class YellowQuestionMarkAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.YELLOW_QUESTION_MARK, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pass
