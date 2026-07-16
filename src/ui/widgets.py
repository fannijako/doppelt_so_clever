from __future__ import annotations

import arcade
from arcade import rect as arect

from src.ui.geometry import Rect
from src.ui.theme import COLORS, DICE_COLORS, with_alpha, mix, dim

CARD_RADIUS = 14
BOX_RADIUS = 7
DIE_RADIUS = 11
BUTTON_RADIUS = 12
PILL_RADIUS = 11

_PIP_GRID = {
    "TL": (0.28, 0.28), "TR": (0.72, 0.28),
    "ML": (0.28, 0.50), "MM": (0.50, 0.50), "MR": (0.72, 0.50),
    "BL": (0.28, 0.72), "BR": (0.72, 0.72),
}
_PIP_PATTERNS = {
    1: ["MM"], 2: ["TL", "BR"], 3: ["TL", "MM", "BR"],
    4: ["TL", "TR", "BL", "BR"], 5: ["TL", "TR", "MM", "BL", "BR"],
    6: ["TL", "TR", "ML", "MR", "BL", "BR"],
}


def pip_offsets(value: int) -> list[tuple[float, float]]:
    return [_PIP_GRID[key] for key in _PIP_PATTERNS.get(value, [])]


def _luminance(color: tuple) -> float:
    return 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]


def _pip_color(background: tuple) -> tuple:
    return (24, 26, 34) if _luminance(background) > 150 else (238, 240, 248)


class Painter:
    def __init__(self, window_height: int, scale: float, font: str | tuple[str, ...] | None) -> None:
        self._h = window_height
        self._scale = scale
        self._font = font
        self._texts: dict[tuple, arcade.Text] = {}

    def px(self, value: float) -> int:
        return max(1, round(value * self._scale))

    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple, width: int = 1) -> None:
        arcade.draw_line(x1, self._h - y1, x2, self._h - y2, color, width)

    def veil(self, width: int, color: tuple) -> None:
        arcade.draw_rect_filled(arect.XYWH(width / 2, self._h / 2, width, self._h), color)

    def round_rect(self, rect: Rect, color: tuple, radius: int) -> None:
        cx, cy = rect.centerx, self._h - rect.centery
        half_w, half_h = rect.w / 2, rect.h / 2
        radius = int(max(1, min(radius, half_w, half_h)))
        arcade.draw_rect_filled(arect.XYWH(cx, cy, rect.w - 2 * radius, rect.h), color)
        arcade.draw_rect_filled(arect.XYWH(cx, cy, rect.w, rect.h - 2 * radius), color)
        for sx in (-1, 1):
            for sy in (-1, 1):
                arcade.draw_circle_filled(cx + sx * (half_w - radius), cy + sy * (half_h - radius),
                                          radius, color, num_segments=24)

    def round_rect_border(self, rect: Rect, fill: tuple, border: tuple, radius: int, width: int = 1) -> None:
        self.round_rect(rect, border, radius)
        self.round_rect(rect.inflate(-2 * width, -2 * width), fill, radius - width)

    def _soft_shadow(self, rect: Rect, radius: int, spread: int = 8, strength: int = 70) -> None:
        spread = self.px(spread)
        for i in range(spread, 0, -2):
            alpha = strength * (1 - i / spread) ** 2
            grown = rect.inflate(2 * i, 2 * i).move(0, i)
            self.round_rect(grown, with_alpha(COLORS["shadow"], alpha / 255), radius + i)

    def _glow(self, rect: Rect, color: tuple, radius: int, spread: int = 10, strength: int = 130) -> None:
        spread = self.px(spread)
        for i in range(spread, 0, -2):
            alpha = strength * (1 - i / spread) ** 2
            self.round_rect(rect.inflate(2 * i, 2 * i), with_alpha(color, alpha / 255), radius + i)

    def card(self, rect: Rect, accent: tuple | None = None) -> None:
        self._soft_shadow(rect, CARD_RADIUS)
        self.round_rect_border(rect, COLORS["panel"], COLORS["panel_border"], CARD_RADIUS, self.px(1))
        if accent is not None:
            accent_bar = Rect(rect.x, rect.y + self.px(16), self.px(5), rect.h - self.px(32))
            self.round_rect(accent_bar, accent, self.px(3))

    def box(self, rect: Rect, fill: tuple, *, border: tuple | None = None,
            label: str = "", label_color: tuple = COLORS["text"],
            crossed: bool = False, circled: bool = False) -> None:
        radius = max(3, self.px(BOX_RADIUS))
        if border is not None:
            self.round_rect_border(rect, fill, border, radius, self.px(1))
        else:
            self.round_rect(rect, fill, radius)
        if label:
            self.text(label, rect.centerx, rect.centery, label_color,
                      max(11, round(rect.w * 0.42)), anchor_x="center", anchor_y="center", bold=True)
        if circled:
            arcade.draw_circle_outline(rect.centerx, self._h - rect.centery,
                                       rect.w // 2 - self.px(3), COLORS["circled"], self.px(3))
        if crossed:
            self._cross(rect)

    def _cross(self, rect: Rect) -> None:
        margin = self.px(9)
        y_top, y_bot = self._h - rect.y - margin, self._h - rect.bottom + margin
        width = self.px(3)
        arcade.draw_line(rect.x + margin, y_top, rect.right - margin, y_bot, COLORS["crossed_mark"], width)
        arcade.draw_line(rect.right - margin, y_top, rect.x + margin, y_bot, COLORS["crossed_mark"], width)

    def die(self, rect: Rect, color_name: str, value: int | None, *,
            available: bool = True, selectable: bool = False, pulse: float = 0.0, hinted: bool = False) -> None:
        base = DICE_COLORS.get(color_name, (180, 180, 185))
        if not available:
            base = dim(base, 96)
        if hinted:
            self._glow(rect, COLORS["hint"], DIE_RADIUS, spread=15, strength=170)
        elif selectable or pulse > 0.0:
            self._glow(rect, COLORS["prompt"], DIE_RADIUS, spread=12,
                       strength=int(90 + 60 * pulse) if pulse > 0 else 70)
        elif available:
            self._soft_shadow(rect, DIE_RADIUS, spread=6, strength=90)
        if hinted:
            hint_ring = self.px(5)
            self.round_rect(rect.inflate(2 * hint_ring, 2 * hint_ring), COLORS["hint"], DIE_RADIUS + hint_ring)
        if selectable:
            ring = self.px(3)
            self.round_rect(rect.inflate(2 * ring, 2 * ring), COLORS["prompt"], DIE_RADIUS + ring)
        self.round_rect(rect, base, DIE_RADIUS)
        highlight = Rect(rect.x + self.px(3), rect.y + self.px(3), rect.w - self.px(6), rect.h // 2 - self.px(2))
        self.round_rect(highlight, with_alpha(mix(base, COLORS["highlight"], 0.22), 0.5), max(4, self.px(8)))
        if value is None:
            self.text("?", rect.centerx, rect.centery, _pip_color(base),
                      round(rect.h * 0.5), anchor_x="center", anchor_y="center", bold=True)
        else:
            self._pips(rect, value, _pip_color(base))

    def _pips(self, rect: Rect, value: int, color: tuple) -> None:
        radius = max(2, round(rect.w * 0.088))
        for fx, fy in pip_offsets(value):
            cx = rect.x + fx * rect.w
            cy = self._h - (rect.y + fy * rect.h)
            arcade.draw_circle_filled(cx, cy, radius, color, num_segments=20)

    def pill(self, rect: Rect, label: str, value: str, accent: tuple, value_size: int = 15) -> None:
        self.round_rect_border(rect, COLORS["panel"], mix(COLORS["panel"], accent, 0.35), PILL_RADIUS, self.px(1))
        self.text(label, rect.centerx, rect.y + self.px(7), COLORS["muted"],
                  max(9, self.px(10)), anchor_x="center", anchor_y="top")
        self.text(value, rect.centerx, rect.bottom - self.px(9), accent,
                  max(12, self.px(value_size)), anchor_x="center", anchor_y="baseline", bold=True)

    def button(self, rect: Rect, label: str, accent: tuple, *,
               state: str = "normal", is_hint: bool = False, size: int = 17) -> None:
        fill = COLORS["button"]
        if state == "hover":
            fill = mix(COLORS["button"], accent, 0.30)
        elif state == "press":
            fill = mix(COLORS["button"], COLORS["shadow"], 0.30)
        if is_hint:
            fill = mix(fill, COLORS["hint"], 0.42)
        border = COLORS["hint"] if is_hint else mix(fill, accent, 0.65)
        if is_hint:
            self._glow(rect, COLORS["hint"], BUTTON_RADIUS, spread=11, strength=130)
        elif state != "press":
            self._soft_shadow(rect, BUTTON_RADIUS, spread=6, strength=60)
        self.round_rect_border(rect, fill, border, BUTTON_RADIUS, self.px(2))
        self.text(label, rect.centerx, rect.centery, mix(COLORS["button_text"], accent, 0.25),
                  max(12, self.px(size)), anchor_x="center", anchor_y="center", bold=True)

    def text(self, string: str, x: int, y: int, color: tuple, size: int, *,
             anchor_x: str = "left", anchor_y: str = "top", bold: bool = False) -> None:
        key = (string, size, tuple(color[:3]), bold, anchor_x, anchor_y)
        label = self._texts.get(key)
        if label is None:
            label = arcade.Text(string, 0, 0, color, size, font_name=self._font,
                                bold=bold, anchor_x=anchor_x, anchor_y=anchor_y)
            self._texts[key] = label
        label.x = x
        label.y = self._h - y
        label.draw()

    def text_width(self, string: str, size: int, bold: bool = False) -> int:
        key = ("_w", string, size, bold)
        label = self._texts.get(key)
        if label is None:
            label = arcade.Text(string, 0, 0, COLORS["text"], size, font_name=self._font, bold=bold)
            self._texts[key] = label
        return round(label.content_width)
