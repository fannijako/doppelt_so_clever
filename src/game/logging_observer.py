from __future__ import annotations

from typing import TYPE_CHECKING

from src.logging_config import GameLogger
from src.game.game_observer import GameObserver

if TYPE_CHECKING:
    from src.dice.dice import Dice

logger = GameLogger(__name__)


class LoggingObserver(GameObserver):
    def on_round_started(self, round_number: int) -> None:
        logger.info("Round started", round_number)

    def on_round_completed(self, round_number: int) -> None:
        logger.info("Round completed", round_number)

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        logger.info("Dice rolled", ", ".join(str(d) for d in dice))

    def on_die_picked(self, die: Dice, discarded: list[Dice]) -> None:
        logger.info("Die picked", die, f"discarded: {discarded}")

    def on_board_updated(self) -> None:
        logger.info("Board updated")

    def on_game_ended(self, score: int) -> None:
        logger.info("Game ended", f"score={score}")
