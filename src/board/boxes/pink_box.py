from src.actions.action_type import ActionType
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class PinkBox:
    def __init__(self, action_filter_limit: int, action: ActionType) -> None:
        logger.debug("Init", "pink box")
        self._validate_input(action_filter_limit, action)
        self.action_filter_limit = action_filter_limit
        self.action = action
        self.value_used = None

    @staticmethod
    def _validate_input(action_filter_limit: int, action: ActionType) -> None:
        if action == ActionType.NONE and action_filter_limit != 0:
            message = "action_filter_limit must be 0 if action is NONE"
            logger.error("Validation", message)
            raise ValueError(message)
        logger.debug("Validation", "valid input")

    def add_dice_value(self, dice_value: int) -> None:
        self.value_used = dice_value
        logger.info("Pink box", dice_value, "added")

    def __str__(self) -> str:
        return f"Pink box: >= {self.action_filter_limit} | {self.action.value}: {self.value_used}"
