from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.board import Board


class GreyQuestionMarkAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.GREY_QUESTION_MARK, is_immediate=True)

    def save(self) -> None:
        raise ValueError("Action cannot be saved")

    def use(self, board: Board, automatic: bool) -> list[Action]:
        return []
