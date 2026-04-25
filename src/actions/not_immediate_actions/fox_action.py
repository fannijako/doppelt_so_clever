from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.not_immediate_actions.not_immediate_actions import NotImmediateActions

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler


class FoxAction(NotImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.FOX)

    def save(self, board: Board) -> None:
        board.foxes += 1

    def use(self, board: Board, input_handler: InputHandler) -> list[Action]:
        raise ValueError("Action cannot be used")
