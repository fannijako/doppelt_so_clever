import random

from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.board import Board

from src.actions.immediate_actions.immediate_actions import ImmediateActions
from src.actions.immediate_actions.blue_question_mark import BlueQuestionMarkAction
from src.actions.immediate_actions.green_question_mark import GreenQuestionMarkAction
from src.actions.immediate_actions.grey_question_mark import GreyQuestionMarkAction
from src.actions.immediate_actions.pink_question_mark import PinkQuestionMarkAction
from src.actions.immediate_actions.yellow_question_mark import YellowQuestionMarkAction


class BlackQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.BLACK_QUESTION_MARK)

    def use(self, board: Board, automatic: bool) -> list[Action]:
        action_to_use = self._pick_action(automatic=automatic)
        return action_to_use().use(board)

    def _pick_action(self, automatic: bool) -> type[Action]:
        if automatic:
            return random.choice(
                [
                    BlueQuestionMarkAction,
                    GreenQuestionMarkAction,
                    GreyQuestionMarkAction,
                    PinkQuestionMarkAction,
                    YellowQuestionMarkAction,
                ]
            )

        color_action_map = {
            "blue": BlueQuestionMarkAction,
            "green": GreenQuestionMarkAction,
            "grey": GreyQuestionMarkAction,
            "pink": PinkQuestionMarkAction,
            "yellow": YellowQuestionMarkAction,
        }

        if (color := input("Enter a color: ")) in color_action_map:
            return color_action_map[color]

        raise ValueError("Invalid color")
