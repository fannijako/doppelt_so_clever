from __future__ import annotations

from pathlib import Path

import arcade

FONT_PATH = Path(__file__).parent / "assets" / "fonts" / "Inter.ttf"
FONT_NAME = "Inter"
FALLBACK_FONT = ("Helvetica Neue", "Arial", "DejaVu Sans")

COLORS = {
    "background_top": (18, 20, 28),
    "background_bottom": (26, 29, 40),
    "panel":          (35, 39, 52),
    "panel_raised":   (43, 48, 64),
    "panel_border":   (54, 59, 78),
    "sunken":         (27, 30, 40),
    "shadow":         (8, 9, 14),
    "text":           (232, 234, 242),
    "dimmed":         (152, 158, 178),
    "muted":          (104, 110, 132),
    "prompt":         (250, 205, 90),
    "score":          (108, 235, 190),
    "crossed_mark":   (236, 238, 246),
    "circled":        (108, 235, 190),
    "box_empty":      (44, 48, 64),
    "button":         (52, 58, 80),
    "button_border":  (84, 94, 126),
    "button_text":    (236, 239, 250),
    "button_hint":    (112, 222, 255),
    "overlay":        (10, 11, 18),
    "highlight":      (255, 255, 255),
}

SECTION_COLORS = {
    "yellow": (245, 199, 64),
    "green":  (76, 190, 110),
    "blue":   (74, 146, 228),
    "pink":   (234, 112, 168),
    "grey":   (150, 158, 178),
}

DICE_COLORS = {
    "green":  (86, 200, 120),
    "blue":   (86, 152, 240),
    "white":  (238, 240, 248),
    "yellow": (250, 206, 72),
    "grey":   (170, 177, 194),
    "pink":   (240, 122, 176),
}

ACTION_COLORS = {
    "none":                 (90, 94, 108),
    "reroll":               (152, 166, 226),
    "reuse":                (140, 212, 152),
    "plus_one":             (250, 212, 112),
    "fox":                  (236, 152, 72),
    "black_question_mark":  (206, 210, 222),
    "blue_question_mark":   (86, 152, 240),
    "green_question_mark":  (86, 200, 120),
    "yellow_question_mark": (250, 206, 72),
    "grey_question_mark":   (170, 177, 194),
    "pink_question_mark":   (240, 122, 176),
}

TYPE = {
    "display": 34,
    "title":   30,
    "heading": 24,
    "body":    18,
    "pill":    20,
    "small":   15,
    "label":   13,
    "tiny":    12,
}

SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}


def load_ui_font() -> str | None:
    if not FONT_PATH.exists():
        return None
    arcade.load_font(str(FONT_PATH))
    return FONT_NAME


def font_name_or_fallback(loaded: str | None) -> str | tuple[str, ...]:
    return loaded if loaded else FALLBACK_FONT


def type_size(name: str, scale: float = 1.0) -> int:
    return max(9, round(TYPE[name] * scale))


def space(name: str, scale: float = 1.0) -> int:
    return max(1, round(SPACE[name] * scale))


def with_alpha(color: tuple, alpha: float) -> tuple:
    return (color[0], color[1], color[2], max(0, min(255, round(alpha * 255))))


def dim(color: tuple, amount: int = 80) -> tuple:
    return tuple(max(channel - amount, 20) for channel in color[:3])


def mix(color_a: tuple, color_b: tuple, ratio: float) -> tuple:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(round(a * (1 - ratio) + b * ratio) for a, b in zip(color_a[:3], color_b[:3]))
