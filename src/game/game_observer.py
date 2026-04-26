from __future__ import annotations

from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from src.dice.dice import Dice


class GameObserver(ABC):
    @abstractmethod
    def on_round_started(self, round_number: int) -> None:
        pass

    @abstractmethod
    def on_round_completed(self, round_number: int) -> None:
        pass

    @abstractmethod
    def on_dice_rolled(self, dice: list[Dice]) -> None:
        pass

    @abstractmethod
    def on_die_picked(self, die: Dice, discarded: list[Dice], available: list[Dice]) -> None:
        pass

    @abstractmethod
    def on_board_updated(self) -> None:
        pass

    @abstractmethod
    def on_game_ended(self, score: int) -> None:
        pass

    @abstractmethod
    def on_action_executed(self, action_description: str) -> None:
        pass

    def close(self) -> None:
        pass
