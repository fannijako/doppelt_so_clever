import logging

from src.actions import Action


class PinkBox:
    def __init__(self, action_filter_limit: int, action: Action) -> None:
        logging.debug("Initializing a pink box")
        self._validate_input(action_filter_limit, action)
        self.action_filter_limit = action_filter_limit
        self.action = action
        self.value_used = None

    @staticmethod
    def _validate_input(action_filter_limit: int, action: Action) -> None:
        if action == Action.NONE and action_filter_limit != 0:
            message = "action_filter_limit must be 0 if action is NONE"
            logging.error(message)
            raise ValueError(message)
        logging.debug("Valid input")

    def add_dice_value(self, dice_value: int) -> None:
        self.value_used = dice_value
        logging.info(f"Dice value {dice_value} added to pink box")

    def __str__(self) -> str:
        return f"Pink box: >= {self.action_filter_limit} | {self.action.value}: {self.value_used}"
