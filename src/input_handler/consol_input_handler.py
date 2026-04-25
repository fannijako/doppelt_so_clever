from typing import Any

from src.logging_config import GameLogger
from src.input_handler.base_input_handler import InputHandler

logger = GameLogger(__name__)


class ConsoleInputHandler(InputHandler):
    def choose_index(self, prompt: str, options: list[Any]) -> int:
        logger.info("Options", ", ".join(f"{i}: {opt}" for i, opt in enumerate(options)))
        return int(input(prompt))

    def confirm(self, prompt: str) -> bool:
        return input(prompt).lower() == 'y'

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        logger.info("Valid values", ", ".join(valid_values))
        return input(prompt)
