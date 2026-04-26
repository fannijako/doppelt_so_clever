from __future__ import annotations

import threading
from typing import Any, TYPE_CHECKING

import pygame

from src.board.board import Board
from src.logging_config import GameLogger
from src.game.game_observer import GameObserver

from src.actions.action_source import ActionSource

if TYPE_CHECKING:
    from src.dice.dice import Dice
    from src.actions.base_action import Action

logger = GameLogger(__name__)


class PygameUI(GameObserver):
    def __init__(self, board: Board):
        self.board = board
        self.current_dice: list[Dice] = []
        self.available_dice: list[Dice] = []

        self._input_event = threading.Event()
        self._input_result: Any = None

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
        self.current_dice = list(dice)
        self.available_dice = list(dice)
        logger.info("UI dice rolled", ", ".join(str(d) for d in dice))
        self._render()

    def on_die_picked(self, die: Dice, discarded: list[Dice], available: list[Dice]) -> None:
        self.available_dice = list(available)
        logger.info("UI die picked", die)
        self._render()

    def on_board_updated(self) -> None:
        self._render()

    def on_game_ended(self, score: int) -> None:
        logger.info("UI game ended", f"score={score}")
        self._render()

    def on_action_executed(self, source: ActionSource, actions: list[Action]) -> None:
        logger.info("UI action executed", source, actions)
        self._render()

    def wait_for_input(self, prompt: str, options: list[Any]) -> int:
        logger.info("UI waiting for input", prompt, f"options={options}")
        self._input_result = None
        self._input_event.clear()
        self._render()
        self._input_event.wait()
        return self._input_result  # type: ignore[return-value]

    def submit_input(self, result: Any) -> None:
        self._input_result = result
        self._input_event.set()

    def close(self) -> None:
        logger.info("PygameUI closed")
        self._input_event.set()
        pygame.quit()

    def _render(self) -> None:
        pygame.event.pump()
