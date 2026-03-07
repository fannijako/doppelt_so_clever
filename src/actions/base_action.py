from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.actions.action_type import ActionType
from src.board.board import Board


class Action(ABC):
    def __init__(self, action_type: ActionType, is_immediate: bool = False):
        self.action_type = action_type
        self.is_immediate = is_immediate

    @abstractmethod
    def save(self, board: Board) -> Action:
        raise NotImplementedError

    @abstractmethod
    def use(self, board: Board, automatic: bool) -> Optional[list[Action]]:
        raise NotImplementedError
