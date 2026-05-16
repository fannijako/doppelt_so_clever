from __future__ import annotations

from src.board.board import Board
from src.game.rl_observer import PromptType, classify_prompt
from src.input_handler.automatic_input_handler import AutomaticInputHandler


class ResourceAwareInputHandler(AutomaticInputHandler):
    def __init__(self, board: Board):
        self._board = board

    def confirm(self, prompt: str) -> bool:
        prompt_type = classify_prompt(prompt)
        if prompt_type == PromptType.PLACE_DIE:
            return True
        if prompt_type == PromptType.USE_REUSE:
            return True
        if prompt_type == PromptType.USE_REROLL:
            return self._board.usable_rerolls >= 2
        if prompt_type == PromptType.USE_PLUS_ONE:
            return self._board.foxes >= 2
        return super().confirm(prompt)
