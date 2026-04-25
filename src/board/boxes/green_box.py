from src.actions.action_type import ActionType
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class GreenBox:
    def __init__(self, value_multiplier: int, action: ActionType, index: int) -> None:
        logger.debug("Init", "green box")
        self._validate_input(value_multiplier)
        self.value_multiplier = value_multiplier
        self.action = action
        self.value_used = None
        self.index = index

    def add_dice_value(self, dice_value: int) -> None:
        self.value_used = dice_value * self.value_multiplier
        logger.info("Green box", dice_value, "added")

    def __str__(self) -> str:
        return f"Green box: {self.value_multiplier}x | {self.action.value}: {self.value_used}"

    @staticmethod
    def _validate_input(value_multiplier: int) -> None:
        if value_multiplier < 1:
            message = "value_multiplier must be at least 1"
            logger.error("Validation", message)
            raise ValueError(message)
        logger.debug("Validation", "valid input")
