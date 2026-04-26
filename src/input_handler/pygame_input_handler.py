from typing import Any

from src.input_handler.base_input_handler import InputHandler


class PygameInputHandler(InputHandler):
    def choose_index(self, prompt: str, options: list[Any]) -> int:
        return 0

    def confirm(self, prompt: str) -> bool:
        return True

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        return valid_values[0] if valid_values else ""
