from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

import pygame

FONT_PATH = Path(__file__).parent / "assets" / "fonts" / "Inter.ttf"
FALLBACK_FAMILIES = "Inter,Helvetica Neue,Arial,DejaVu Sans"

COLORS = {
    "background":     (22, 24, 32),
    "panel":          (36, 39, 52),
    "panel_border":   (52, 56, 74),
    "sunken":         (28, 30, 40),
    "shadow":         (10, 11, 16),
    "text":           (232, 234, 242),
    "dimmed":         (150, 156, 176),
    "muted":          (104, 110, 132),
    "prompt":         (250, 205, 90),
    "score":          (108, 235, 190),
    "crossed":        (224, 84, 84),
    "circled":        (72, 202, 140),
    "box_empty":      (46, 50, 66),
    "button":         (52, 58, 80),
    "button_hover":   (72, 82, 116),
    "button_press":   (42, 48, 68),
    "button_text":    (236, 239, 250),
    "button_hint":    (112, 222, 255),
    "overlay":        (12, 13, 20),
    "white":          (232, 234, 242),
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
    "none":                (90, 94, 108),
    "reroll":              (152, 166, 226),
    "reuse":               (140, 212, 152),
    "plus_one":            (250, 212, 112),
    "fox":                 (236, 152, 72),
    "black_question_mark": (206, 210, 222),
    "blue_question_mark":  (86, 152, 240),
    "green_question_mark": (86, 200, 120),
    "yellow_question_mark": (250, 206, 72),
    "grey_question_mark":  (170, 177, 194),
    "pink_question_mark":  (240, 122, 176),
}


@dataclass(frozen=True)
class Fonts:
    tiny: pygame.font.Font
    small: pygame.font.Font
    body: pygame.font.Font
    label: pygame.font.Font
    heading: pygame.font.Font
    display: pygame.font.Font


def _load_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    if not pygame.font.get_init():
        pygame.font.init()
    if FONT_PATH.exists():
        font = pygame.font.Font(str(FONT_PATH), size)
        font.set_bold(bold)
        return font
    return pygame.font.SysFont(FALLBACK_FAMILIES, size, bold=bold)


def load_fonts(scale: float = 1.0) -> Fonts:
    def sized(pixels: int) -> int:
        return max(9, round(pixels * scale))

    return Fonts(
        tiny=_load_font(sized(13)),
        small=_load_font(sized(15)),
        body=_load_font(sized(18)),
        label=_load_font(sized(13), bold=True),
        heading=_load_font(sized(26), bold=True),
        display=_load_font(sized(34), bold=True),
    )


def dim(color: tuple, amount: int = 80) -> tuple:
    return tuple(max(channel - amount, 24) for channel in color[:3])


def mix(color_a: tuple, color_b: tuple, ratio: float) -> tuple:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(round(a * (1 - ratio) + b * ratio) for a, b in zip(color_a[:3], color_b[:3]))
