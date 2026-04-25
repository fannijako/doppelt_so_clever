from typing import Any
from abc import ABC, abstractmethod


class InputHandler(ABC):
    @abstractmethod
    def choose_index(self, prompt: str, options: list[Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def confirm(self, prompt: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        raise NotImplementedError
