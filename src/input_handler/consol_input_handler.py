from typing import Any

from src.logging_config import GameLogger
from src.input_handler.base_input_handler import InputHandler

logger = GameLogger(__name__)


class ConsoleInputHandler(InputHandler):
    def choose_index(self, prompt: str, options: list[Any]) -> int:
        logger.info("Options", ", ".join(f"{i}: {opt}" for i, opt in enumerate(options)))
        while not (index := input(prompt)).isdigit() or int(index) < 0 or int(index) >= len(options):
            logger.error("Invalid input", "Please enter a valid number")
        return int(index)

    def confirm(self, prompt: str) -> bool:
        while not (answer := input(prompt).lower()) in ['y', 'n']:
            logger.error("Invalid input", "Please enter 'y' or 'n'")
        return answer == 'y'

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        logger.info("Valid values", ", ".join(valid_values))
        while not (value := input(prompt)) in valid_values:
            logger.error("Invalid input", "Please enter a valid value")
        return value
