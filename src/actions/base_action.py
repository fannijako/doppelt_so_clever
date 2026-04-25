from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from src.actions.action_type import ActionType

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler


class Action(ABC):
    def __init__(self, action_type: ActionType, is_immediate: bool = False):
        self.action_type = action_type
        self.is_immediate = is_immediate

    def __repr__(self) -> str:
        return f"{self.action_type.value}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        return self.action_type == other.action_type

    @abstractmethod
    def save(self, board: Board) -> Action:
        raise NotImplementedError

    @abstractmethod
    def use(self, board: Board, input_handler: InputHandler) -> Optional[list[Action]]:
        raise NotImplementedError
