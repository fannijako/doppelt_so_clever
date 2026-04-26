from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RenderSnapshot:  # pylint: disable=too-many-instance-attributes
    board_data: dict
    dice: list
    available_dice: list
    round_number: int
    prompt: str
    options: list
    is_waiting: bool
    score: int | None
    is_game_over: bool
