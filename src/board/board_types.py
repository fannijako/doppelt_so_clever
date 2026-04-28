from __future__ import annotations

from typing import TypedDict


class BlueBoxDict(TypedDict):
    value_used: int | None
    max_limit: int
    action: str


class GreenBoxDict(TypedDict):
    value_used: int | None
    multiplier: int
    action: str


class PinkBoxDict(TypedDict):
    value_used: int | None
    filter_limit: int | None
    action: str


class YellowBoxDict(TypedDict):
    value: int
    row: int
    col: int
    circled: bool
    crossed: bool


class GreyBoxDict(TypedDict):
    color: str
    number: int
    crossed: bool


class PositionalActionDict(TypedDict):
    action: str
    available: bool


class ResourceDict(TypedDict):
    gained: int
    usable: int


class BoardDict(TypedDict):
    blue: list[BlueBoxDict]
    green: list[GreenBoxDict]
    pink: list[PinkBoxDict]
    yellow: list[YellowBoxDict]
    yellow_row_actions: dict[int, PositionalActionDict]
    yellow_col_actions: dict[int, PositionalActionDict]
    grey: list[GreyBoxDict]
    grey_col_actions: dict[int, PositionalActionDict]
    foxes: int
    rerolls: ResourceDict
    reuses: ResourceDict
    plus_ones: ResourceDict
