from __future__ import annotations

from typing import Any

from src.dice.dice import Dice


def build_pick_map(options: list[Any], dice_pool: list[Dice]) -> dict[int, int]:
    pick_map: dict[int, int] = {}
    for index, option in enumerate(options):
        if isinstance(option, Dice):
            pick_map[id(option)] = index
        elif isinstance(option, str):
            for die in dice_pool:
                if die.color and str(die.color.value) == option and id(die) not in pick_map:
                    pick_map[id(die)] = index
    return pick_map


def die_index_at(dice_targets: list[tuple], pick_map: dict[int, int],
                 position: tuple[int, int]) -> int | None:
    x, y = position
    for die, rect in dice_targets:
        if rect.collidepoint(x, y) and id(die) in pick_map:
            return pick_map[id(die)]
    return None


def button_index_at(button_rects: list, position: tuple[int, int]) -> int | None:
    x, y = position
    for index, rect in enumerate(button_rects):
        if rect.collidepoint(x, y):
            return index
    return None
