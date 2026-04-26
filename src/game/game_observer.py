from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.dice.dice import Dice


class GameObserver:
    def on_round_started(self, round_number: int) -> None:
        pass

    def on_round_completed(self, round_number: int) -> None:
        pass

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        pass

    def on_die_picked(self, die: Dice, discarded: list[Dice]) -> None:
        pass

    def on_board_updated(self) -> None:
        pass

    def on_game_ended(self, score: int) -> None:
        pass
