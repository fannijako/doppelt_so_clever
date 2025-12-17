import logging

from src.actions import Action


class GreenBox:
    def __init__(self, value_multiplier: int, action: Action) -> None:
        logging.debug("Initializing a green box")
        self._validate_input(value_multiplier)
        self.value_multiplier = value_multiplier
        self.action = action
        self.value_used = None

    def add_dice_value(self, dice_value: int) -> None:
        self.value_used = dice_value * self.value_multiplier
        logging.info(f"Dice value {dice_value} added to green box")

    def __str__(self) -> str:
        return f"Green box: {self.value_multiplier}x | {self.action.value}: {self.value_used}"

    @staticmethod
    def _validate_input(value_multiplier: int) -> None:
        if value_multiplier < 1:
            message = "value_multiplier must be at least 1"
            logging.error(message)
            raise ValueError(message)
        logging.debug("Valid input")
