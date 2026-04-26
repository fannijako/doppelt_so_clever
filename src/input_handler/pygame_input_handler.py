from __future__ import annotations

from typing import Any, TYPE_CHECKING

from src.input_handler.base_input_handler import InputHandler

if TYPE_CHECKING:
    from src.ui.pygame_ui import PygameUI


class PygameInputHandler(InputHandler):
    def __init__(self, ui: PygameUI):
        self._ui = ui

    def choose_index(self, prompt: str, options: list[Any]) -> int:
        return self._ui.wait_for_input(prompt, options)

    def confirm(self, prompt: str) -> bool:
        result = self._ui.wait_for_input(prompt, ["yes", "no"])
        return result == 0

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        index = self._ui.wait_for_input(prompt, valid_values)
        return valid_values[index] if valid_values else ""
