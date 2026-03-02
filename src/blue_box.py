import logging

from src.actions.actions import ActionType


class BlueBox:
    def __init__(self, maximum_value_limit: int, action: ActionType) -> None:
        logging.debug("Initializing a blue box")
        self._validate_input(maximum_value_limit)
        self.maximum_value_limit = maximum_value_limit
        self.action = action
        self.value_used = None

    @staticmethod
    def _validate_input(maximum_value_limit: int) -> None:
        if not 1 <= maximum_value_limit <= 12:
            message = "maximum_value_limit must be between 1 and 12"
            logging.error(message)
            raise ValueError(message)
        logging.debug("Valid input")

    def add_dice_value(self, blue_dice_value: int, white_dice_value: int) -> None:
        new_value = blue_dice_value + white_dice_value
        if new_value > self.maximum_value_limit:
            logging.error("Dice value is too high")
            return

        self.value_used = new_value
        logging.info(
            f"Dice value {blue_dice_value} + {white_dice_value} = {self.value_used}"
            " added to blue box"
        )

    def __str__(self) -> str:
        return (
            f"blue box: {self.maximum_value_limit} >= | {self.action.value}: {self.value_used}"
        )
