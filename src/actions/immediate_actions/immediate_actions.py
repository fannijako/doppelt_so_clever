from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.base_action import Action
from src.actions.action_type import ActionType

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler


class ImmediateActions(Action):
    def __init__(self, action_type: ActionType):
        super().__init__(
            action_type=action_type,
            is_immediate=True
        )

    def save(self, board: Board) -> None:
        raise ValueError("Action cannot be saved")

    def use(self, board: Board, input_handler: InputHandler) -> list[Action]:
        raise NotImplementedError
