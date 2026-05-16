from __future__ import annotations

from typing import TYPE_CHECKING

from src.dice.dice_color import DiceColor

if TYPE_CHECKING:
    from src.board.board import Board

_COLOR_TO_PART_ATTR: dict[DiceColor, str] = {
    DiceColor.BLUE: "blue_board_part",
    DiceColor.GREEN: "green_board_part",
    DiceColor.PINK: "pink_board_part",
    DiceColor.YELLOW: "yellow_board_part",
    DiceColor.GREY: "grey_board_part",
}


def color_from_value(value: str) -> DiceColor | None:
    try:
        return DiceColor(value)
    except ValueError:
        return None


def empty_box_count(board: Board, color: DiceColor) -> int:
    attr = _COLOR_TO_PART_ATTR.get(color)
    if attr is None:
        return -1
    part = getattr(board, attr)
    if color == DiceColor.YELLOW:
        return sum(1 for box in part.boxes if not box.is_circled)
    if color == DiceColor.GREY:
        return sum(1 for box in part.boxes if not box.is_crossed)
    return sum(1 for box in part.boxes if box.value_used is None)


def part_score(board: Board, color: DiceColor) -> int:
    attr = _COLOR_TO_PART_ATTR.get(color)
    if attr is None:
        return 0
    return getattr(board, attr).evaluate()


def pick_value_by_priority(
    valid_values: list[str], key,
) -> str | None:
    candidates: list[tuple[str, DiceColor]] = []
    for value in valid_values:
        color = color_from_value(value)
        if color is not None and color in _COLOR_TO_PART_ATTR:
            candidates.append((value, color))
    if not candidates:
        return None
    return max(candidates, key=lambda pair: key(pair[1]))[0]
