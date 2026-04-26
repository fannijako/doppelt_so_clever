from __future__ import annotations

from typing import TYPE_CHECKING

from src.game.game_observer import GameObserver

if TYPE_CHECKING:
    from src.dice.dice import Dice


class CompositeObserver(GameObserver):
    def __init__(self, observers: list[GameObserver] | None = None):
        self._observers: list[GameObserver] = list(observers) if observers else []

    def add(self, observer: GameObserver) -> None:
        self._observers.append(observer)

    def on_round_started(self, round_number: int) -> None:
        for observer in self._observers:
            observer.on_round_started(round_number)

    def on_round_completed(self, round_number: int) -> None:
        for observer in self._observers:
            observer.on_round_completed(round_number)

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        for observer in self._observers:
            observer.on_dice_rolled(dice)

    def on_die_picked(self, die: Dice, discarded: list[Dice], available: list[Dice]) -> None:
        for observer in self._observers:
            observer.on_die_picked(die, discarded, available)

    def on_board_updated(self) -> None:
        for observer in self._observers:
            observer.on_board_updated()

    def on_game_ended(self, score: int) -> None:
        for observer in self._observers:
            observer.on_game_ended(score)

    def on_action_executed(self, action_description: str) -> None:
        for observer in self._observers:
            observer.on_action_executed(action_description)

    def close(self) -> None:
        for observer in self._observers:
            observer.close()
