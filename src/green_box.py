import logging

from src.actions import Action


class GreenBox:
    def __init__(self, value_multiplier: int, action: Action) -> None:
        logging.debug("Initializing a green box")
        self.value_multiplier = value_multiplier
        self.action = action
        self.value_used = None

    def add_die_value(self, die_value: int) -> None:
        self.value_used = die_value * self.value_multiplier
        logging.info(f"Die value {die_value} added to green box")

    def __str__(self) -> str:
        return f"Green box: {self.value_multiplier}x | {self.action.value}: {self.value_used}"
