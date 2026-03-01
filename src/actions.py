# pylint: disable=too-few-public-methods

from enum import Enum


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


class ReRollAction(Action):
    def __init__(self, action_type: ActionType = ActionType.REROLL, is_immediate: bool = False):
        super().__init__(action_type, is_immediate)


class ReUseAction(Action):
    def __init__(self, action_type: ActionType = ActionType.REUSE, is_immediate: bool = False):
        super().__init__(action_type, is_immediate)


class PlusOneAction(Action):
    def __init__(self, action_type: ActionType = ActionType.PLUS_ONE, is_immediate: bool = False):
        super().__init__(action_type, is_immediate)


class BlackQuestionMarkAction(Action):
    def __init__(self, action_type: ActionType = ActionType.BLACK_QUESTION_MARK, is_immediate: bool = True):
        super().__init__(action_type, is_immediate)


class GreenQuestionMarkAction(Action):
    def __init__(self, action_type: ActionType = ActionType.GREEN_QUESTION_MARK, is_immediate: bool = True):
        super().__init__(action_type, is_immediate)


class YellowQuestionMarkAction(Action):
    def __init__(self, action_type: ActionType = ActionType.YELLOW_QUESTION_MARK, is_immediate: bool = True):
        super().__init__(action_type, is_immediate)


class BlueQuestionMarkAction(Action):
    def __init__(self, action_type: ActionType = ActionType.BLUE_QUESTION_MARK, is_immediate: bool = True):
        super().__init__(action_type, is_immediate)


class GreyQuestionMarkAction(Action):
    def __init__(self, action_type: ActionType = ActionType.GREY_QUESTION_MARK, is_immediate: bool = True):
        super().__init__(action_type, is_immediate)


class PinkQuestionMarkAction(Action):
    def __init__(self, action_type: ActionType = ActionType.PINK_QUESTION_MARK, is_immediate: bool = True):
        super().__init__(action_type, is_immediate)


class FoxAction(Action):
    def __init__(self, action_type: ActionType = ActionType.FOX, is_immediate: bool = True):
        super().__init__(action_type, is_immediate)
