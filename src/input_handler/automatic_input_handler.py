import random
from typing import Any

from src.logging_config import GameLogger
from src.input_handler.base_input_handler import InputHandler

logger = GameLogger(__name__)


class AutomaticInputHandler(InputHandler):
    def choose_index(self, prompt: str, options: list[Any]) -> int:
        index = random.randint(0, len(options) - 1)
        logger.debug("Random choice", f"index={index}", f"from {len(options)} options")
        return index

    def confirm(self, prompt: str) -> bool:
        result = random.choice([True, False])
        logger.debug("Random confirm", result)
        return result

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        value = random.choice(valid_values)
        logger.debug("Random value", value)
        return value
