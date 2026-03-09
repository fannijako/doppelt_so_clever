from src.actions.action_type import ActionType


class ActionMap:  # pylint: disable=too-few-public-methods
    _map: dict | None = None

    @classmethod
    def get(cls, action_type: ActionType):
        if cls._map is None:
            cls._initialize()
        action_class = cls._map.get(action_type)
        return action_class() if action_class is not None else None

    @classmethod
    def _initialize(cls):
        # pylint: disable=import-outside-toplevel
        from src.actions.not_immediate_actions.reroll_action import ReRollAction
        from src.actions.not_immediate_actions.reuse_action import ReUseAction
        from src.actions.not_immediate_actions.plus_one_action import PlusOneAction
        from src.actions.not_immediate_actions.fox_action import FoxAction
        from src.actions.immediate_actions.black_question_mark import BlackQuestionMarkAction
        from src.actions.immediate_actions.green_question_mark import GreenQuestionMarkAction
        from src.actions.immediate_actions.yellow_question_mark import YellowQuestionMarkAction
        from src.actions.immediate_actions.blue_question_mark import BlueQuestionMarkAction
        from src.actions.immediate_actions.grey_question_mark import GreyQuestionMarkAction
        from src.actions.immediate_actions.pink_question_mark import PinkQuestionMarkAction
        cls._map = {
            ActionType.REROLL: ReRollAction,
            ActionType.REUSE: ReUseAction,
            ActionType.PLUS_ONE: PlusOneAction,
            ActionType.FOX: FoxAction,
            ActionType.BLACK_QUESTION_MARK: BlackQuestionMarkAction,
            ActionType.GREEN_QUESTION_MARK: GreenQuestionMarkAction,
            ActionType.YELLOW_QUESTION_MARK: YellowQuestionMarkAction,
            ActionType.BLUE_QUESTION_MARK: BlueQuestionMarkAction,
            ActionType.GREY_QUESTION_MARK: GreyQuestionMarkAction,
            ActionType.PINK_QUESTION_MARK: PinkQuestionMarkAction,
            ActionType.NONE: None,
        }
