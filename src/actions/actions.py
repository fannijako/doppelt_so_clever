# pylint: disable=too-few-public-methods

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.board import Board


class ActionType(Enum):
    NONE = "none"
    REROLL = "reroll"
    REUSE = "reuse"
    PLUS_ONE = "plus_one"
    BLACK_QUESTION_MARK = "black_question_mark"
    GREEN_QUESTION_MARK = "green_question_mark"
    YELLOW_QUESTION_MARK = "yellow_question_mark"
    BLUE_QUESTION_MARK = "blue_question_mark"
    GREY_QUESTION_MARK = "grey_question_mark"
    PINK_QUESTION_MARK = "pink_question_mark"
    FOX = "fox"


class Action:
    def __init__(self, action_type: ActionType, is_immediate: bool = False):
        self.action_type = action_type
        self.is_immediate = is_immediate

    def save(self):
        raise NotImplementedError

    def use(self, board: Board) -> list[Action]:
        raise NotImplementedError


class ReRollAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.REROLL, is_immediate=False)

    def save(self):
        pass

    def use(self, board: Board) -> list[Action]:
        pass


class ReUseAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.REUSE, is_immediate=False)

    def save(self):
        pass

    def use(self, board: Board) -> list[Action]:
        pass


class PlusOneAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.PLUS_ONE, is_immediate=False)

    def save(self):
        pass

    def use(self, board: Board) -> list[Action]:
        pass


class BlackQuestionMarkAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.BLACK_QUESTION_MARK, is_immediate=True)

    def save(self):
        pass

    def use(self, board: Board) -> list[Action]:
        pass


class GreenQuestionMarkAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.GREEN_QUESTION_MARK, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pass


class YellowQuestionMarkAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.YELLOW_QUESTION_MARK, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pass


class BlueQuestionMarkAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.BLUE_QUESTION_MARK, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pass


class GreyQuestionMarkAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.GREY_QUESTION_MARK, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pass


class FoxAction(Action):
    def __init__(self):
        super().__init__(action_type=ActionType.FOX, is_immediate=True)

    def save(self):
        raise ValueError("Action cannot be saved")

    def use(self, board: Board) -> list[Action]:
        pass
