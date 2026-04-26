from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.board.board import Board
from src.logging_config import GameLogger
from src.game.game_observer import GameObserver

if TYPE_CHECKING:
    from src.dice.dice import Dice

logger = GameLogger(__name__)


class PygameUI(GameObserver):
    def __init__(self, board: Board):
        self.board = board

        pygame.init()
        pygame.display.set_allow_screensaver(True)
        pygame.display.set_caption("Doppelt So Clever")

    def on_round_started(self, round_number: int) -> None:
        logger.info("UI round started", round_number)
        self._render()

    def on_round_completed(self, round_number: int) -> None:
        logger.info("UI round completed", round_number)
        self._render()

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        logger.info("UI dice rolled", ", ".join(str(d) for d in dice))
        self._render()

    def on_die_picked(self, die: Dice, discarded: list[Dice]) -> None:
        logger.info("UI die picked", die)
        self._render()

    def on_board_updated(self) -> None:
        self._render()

    def on_game_ended(self, score: int) -> None:
        logger.info("UI game ended", f"score={score}")
        self._render()

    def close(self) -> None:
        logger.info("PygameUI closed")
        pygame.quit()

    def _render(self) -> None:
        pygame.event.pump()
