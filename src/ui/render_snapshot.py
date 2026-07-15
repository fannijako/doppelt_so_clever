from __future__ import annotations

from dataclasses import dataclass, field

from src.board.board_types import BoardDict


@dataclass
class RenderSnapshot:  # pylint: disable=too-many-instance-attributes
    board_data: BoardDict
    dice: list
    available_dice: list
    picked_dice: list
    discarded_dice: list
    round_number: int
    is_active_round: bool
    subround: int
    prompt: str
    options: list
    is_waiting: bool
    score: int | None
    is_game_over: bool
    won_actions: list[dict]
    popup_notifications: list[dict]
    hint_index: int | None = None
    display_score: int | None = None
    die_pulses: dict[int, float] = field(default_factory=dict)
    pressed_index: int | None = None
    selectable_die_ids: set = field(default_factory=set)
    show_help: bool = False
