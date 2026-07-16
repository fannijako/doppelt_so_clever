from __future__ import annotations

from dataclasses import dataclass

from src.ui.geometry import Rect

BASE_WIDTH = 1280
BASE_HEIGHT = 800
MIN_SCALE = 0.70
MAX_SCALE = 1.6

MARGIN = 26
GAP = 16
TOP_BAR_HEIGHT = 78
TRAY_HEIGHT = 124
ACTION_HEIGHT = 104
BOARD_GAP = 16

SIDE_COLUMN_RATIO = 0.235
MIN_PANEL_WIDTH = 150
MIN_BOARD_HEIGHT = 150

TOAST_WIDTH = 250
TOAST_HEIGHT = 34
TOAST_GAP = 8
MAX_TOASTS = 2


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class Layout:  # pylint: disable=too-many-instance-attributes
    width: int
    height: int
    scale: float
    margin: int
    top_bar: Rect
    yellow: Rect
    mid: Rect
    grey: Rect
    tray: Rect
    action: Rect

    @property
    def board_columns(self) -> tuple[Rect, Rect, Rect]:
        return self.yellow, self.mid, self.grey

    @classmethod
    def compute(cls, width: int, height: int) -> "Layout":
        scale = _clamp(min(width / BASE_WIDTH, height / BASE_HEIGHT), MIN_SCALE, MAX_SCALE)
        margin = round(MARGIN * scale)
        gap = round(GAP * scale)
        top_h = round(TOP_BAR_HEIGHT * scale)
        tray_h = round(TRAY_HEIGHT * scale)
        action_h = round(ACTION_HEIGHT * scale)

        top_bar = Rect(margin, round(18 * scale), width - 2 * margin, top_h)
        action = Rect(margin, height - margin - action_h, width - 2 * margin, action_h)
        tray = Rect(margin, action.y - gap - tray_h, width - 2 * margin, tray_h)

        board_y = top_h + gap
        board_h = max(MIN_BOARD_HEIGHT, tray.y - gap - board_y)
        yellow, mid, grey = cls._board_columns(width, board_y, board_h, margin, round(BOARD_GAP * scale))

        return cls(width=width, height=height, scale=scale, margin=margin,
                   top_bar=top_bar, yellow=yellow, mid=mid, grey=grey, tray=tray, action=action)

    @staticmethod
    def _board_columns(width: int, board_y: int, board_h: int, margin: int, gap: int) -> tuple[Rect, Rect, Rect]:
        inner_w = width - 2 * margin
        side_w = max(round((inner_w - 2 * gap) * SIDE_COLUMN_RATIO), MIN_PANEL_WIDTH)
        mid_w = max(inner_w - 2 * gap - 2 * side_w, MIN_PANEL_WIDTH)
        return (
            Rect(margin, board_y, side_w, board_h),
            Rect(margin + side_w + gap, board_y, mid_w, board_h),
            Rect(margin + side_w + gap + mid_w + gap, board_y, side_w, board_h),
        )

    def toast_slots(self, count: int) -> list[Rect]:
        shown = min(count, MAX_TOASTS)
        if shown == 0:
            return []
        gap = round(TOAST_GAP * self.scale)
        height = round(TOAST_HEIGHT * self.scale)
        width = round(TOAST_WIDTH * self.scale)
        left = self.grey.right - width
        top = self.grey.y + round(46 * self.scale)
        return [Rect(left, top + index * (height + gap), width, height) for index in range(shown)]
