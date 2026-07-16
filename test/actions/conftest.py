from typing import Any

import pytest

from src.input_handler.base_input_handler import InputHandler


class StubInputHandler(InputHandler):
    def choose_index(self, prompt: str, options: list[Any]) -> int:
        return 0

    def confirm(self, prompt: str) -> bool:
        return True

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        return valid_values[0]


@pytest.fixture()
def stub_input_handler():
    return StubInputHandler()
