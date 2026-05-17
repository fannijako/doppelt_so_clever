from __future__ import annotations

from src.board.board import Board
from src.game.rl_observer import PromptType, classify_prompt
from src.input_handler.automatic_input_handler import AutomaticInputHandler
from src.input_handler.heuristics._board_stats import (
    empty_box_count,
    part_score,
    pick_value_by_priority,
)

_COLOR_PROMPTS = {
    PromptType.PICK_DIE_COLOR,
    PromptType.PICK_COLOR_SUBSTITUTE,
    PromptType.PICK_COLOR_QUESTION_MARK,
}


class FoxBalancingInputHandler(AutomaticInputHandler):
    def __init__(self, board: Board):
        self._board = board

    def confirm(self, prompt: str) -> bool:
        if classify_prompt(prompt) == PromptType.PLACE_DIE:
            return True
        return super().confirm(prompt)

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        if classify_prompt(prompt) in _COLOR_PROMPTS:
            choice = pick_value_by_priority(
                valid_values, key=self._lowest_score_key,
            )
            if choice is not None:
                return choice
        return super().choose_value(prompt, valid_values)

    def _lowest_score_key(self, color) -> tuple[int, int]:
        return (-part_score(self._board, color), empty_box_count(self._board, color))
