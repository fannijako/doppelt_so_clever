from __future__ import annotations

from dataclasses import dataclass

import pygame

MARGIN = 18
GAP = 14
TITLE_HEIGHT = 50
STATUS_HEIGHT = 36
BOTTOM_RESERVE = 152
MIN_PANEL_WIDTH = 168
MIN_ROW_HEIGHT = 118

POPUP_WIDTH = 300
POPUP_HEIGHT = 46
POPUP_GAP = 8
POPUP_TOP = 66


@dataclass(frozen=True)
class Layout:
    width: int
    height: int
    title_baseline: int
    top_panels: tuple
    won_actions: pygame.Rect
    dice_panel: pygame.Rect
    status_y: int
    prompt_y: int

    @classmethod
    def compute(cls, width: int, height: int) -> "Layout":
        title_bottom = TITLE_HEIGHT
        region_height = height - title_bottom - STATUS_HEIGHT - BOTTOM_RESERVE
        row_height = max((region_height - GAP) // 2, MIN_ROW_HEIGHT)

        panel_width = max((width - 2 * MARGIN - 2 * GAP) // 3, MIN_PANEL_WIDTH)
        top_panels = tuple(
            pygame.Rect(MARGIN + index * (panel_width + GAP), title_bottom, panel_width, row_height)
            for index in range(3)
        )

        second_row_y = title_bottom + row_height + GAP
        won_actions = pygame.Rect(MARGIN, second_row_y, 2 * panel_width + GAP, row_height)
        dice_panel = pygame.Rect(MARGIN + 2 * (panel_width + GAP), second_row_y, panel_width, row_height)

        status_y = second_row_y + row_height + 8
        prompt_y = status_y + STATUS_HEIGHT

        return cls(
            width=width,
            height=height,
            title_baseline=12,
            top_panels=top_panels,
            won_actions=won_actions,
            dice_panel=dice_panel,
            status_y=status_y,
            prompt_y=prompt_y,
        )

    def popup_origin(self) -> tuple[int, int]:
        return self.width - POPUP_WIDTH - MARGIN, POPUP_TOP
