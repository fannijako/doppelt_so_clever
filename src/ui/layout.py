from __future__ import annotations

from dataclasses import dataclass

import pygame

MARGIN = 18
GAP = 14
TITLE_HEIGHT = 52
STATUS_HEIGHT = 34
BOTTOM_RESERVE = 150
MIN_PANEL_WIDTH = 150
MIN_ROW_HEIGHT = 96

SIDE_COLUMN_RATIO = 0.24
TOP_BAND_RATIO = 0.60
WON_COLUMN_RATIO = 0.56

POPUP_HEIGHT = 40
POPUP_GAP = 8
MAX_POPUPS = 3

BASE_WIDTH = 1280
BASE_HEIGHT = 800
MIN_SCALE = 0.72
MAX_SCALE = 1.6


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _top_panels(width: int, title_h: int, top_h: int, margin: int, gap: int) -> tuple:
    inner_w = width - 2 * margin
    side_w = max(round((inner_w - 2 * gap) * SIDE_COLUMN_RATIO), MIN_PANEL_WIDTH)
    mid_w = max(inner_w - 2 * gap - 2 * side_w, MIN_PANEL_WIDTH)
    return (
        pygame.Rect(margin, title_h, side_w, top_h),
        pygame.Rect(margin + side_w + gap, title_h, mid_w, top_h),
        pygame.Rect(margin + side_w + gap + mid_w + gap, title_h, side_w, top_h),
    )


def _bottom_panels(width: int, bottom_y: int, bottom_h: int, margin: int, gap: int) -> tuple:
    inner_w = width - 2 * margin
    won_w = max(round((inner_w - gap) * WON_COLUMN_RATIO), MIN_PANEL_WIDTH)
    won_actions = pygame.Rect(margin, bottom_y, won_w, bottom_h)
    dice_panel = pygame.Rect(margin + won_w + gap, bottom_y, inner_w - won_w - gap, bottom_h)
    return won_actions, dice_panel


@dataclass(frozen=True)
class Layout:  # pylint: disable=too-many-instance-attributes
    width: int
    height: int
    scale: float
    title_baseline: int
    divider_y: int
    top_panels: tuple
    won_actions: pygame.Rect
    dice_panel: pygame.Rect
    status_y: int
    prompt_y: int

    @classmethod
    def compute(cls, width: int, height: int) -> "Layout":
        scale = _clamp(min(width / BASE_WIDTH, height / BASE_HEIGHT), MIN_SCALE, MAX_SCALE)
        margin = round(MARGIN * scale)
        gap = round(GAP * scale)
        title_h = round(TITLE_HEIGHT * scale)

        usable_h = height - title_h - round(BOTTOM_RESERVE * scale) - gap
        top_h = max(round(usable_h * TOP_BAND_RATIO), MIN_ROW_HEIGHT)
        bottom_h = max(usable_h - top_h, MIN_ROW_HEIGHT)
        bottom_y = title_h + top_h + gap
        won_actions, dice_panel = _bottom_panels(width, bottom_y, bottom_h, margin, gap)
        status_y = bottom_y + bottom_h + round(10 * scale)

        return cls(
            width=width, height=height, scale=scale,
            title_baseline=round(12 * scale),
            divider_y=title_h - round(7 * scale),
            top_panels=_top_panels(width, title_h, top_h, margin, gap),
            won_actions=won_actions, dice_panel=dice_panel,
            status_y=status_y, prompt_y=status_y + round(STATUS_HEIGHT * scale),
        )

    def popup_origin(self) -> tuple[int, int]:
        pad = round(MARGIN * self.scale)
        legend_reserve = round(30 * self.scale)
        stack_height = MAX_POPUPS * round((POPUP_HEIGHT + POPUP_GAP) * self.scale)
        top = self.won_actions.bottom - legend_reserve - stack_height
        return self.won_actions.x + pad, top

    def popup_width(self) -> int:
        return self.won_actions.w - 2 * round(MARGIN * self.scale)
