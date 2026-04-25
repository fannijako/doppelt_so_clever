from typing import Any

from src.input_handler.base_input_handler import InputHandler
from model.model import DoppeltSoCleverModel


class ModelInputHandler(InputHandler):
    def __init__(self, model: DoppeltSoCleverModel):
        self.model = model

    def choose_index(self, prompt: str, options: list[Any]) -> int:
        return self.model.predict(list(range(len(options))))

    def confirm(self, prompt: str) -> bool:
        return self.model.predict(["y", "n"])

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        return self.model.predict(valid_values)
