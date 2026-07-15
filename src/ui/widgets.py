from __future__ import annotations

import pygame

from src.ui.theme import COLORS, DICE_COLORS, dim

CARD_RADIUS = 10
CARD_SHADOW_OFFSET = 4
CARD_ACCENT_HEIGHT = 4
DIE_RADIUS = 9
PIP_RADIUS_RATIO = 0.092
BUTTON_RADIUS = 9
PILL_RADIUS = 7

_PIP_GRID = {
    "TL": (0.30, 0.30), "TM": (0.50, 0.30), "TR": (0.70, 0.30),
    "ML": (0.30, 0.50), "MM": (0.50, 0.50), "MR": (0.70, 0.50),
    "BL": (0.30, 0.70), "BM": (0.50, 0.70), "BR": (0.70, 0.70),
}

_PIP_PATTERNS = {
    1: ["MM"],
    2: ["TL", "BR"],
    3: ["TL", "MM", "BR"],
    4: ["TL", "TR", "BL", "BR"],
    5: ["TL", "TR", "MM", "BL", "BR"],
    6: ["TL", "TR", "ML", "MR", "BL", "BR"],
}


def pip_offsets(value: int) -> list[tuple[float, float]]:
    return [_PIP_GRID[key] for key in _PIP_PATTERNS.get(value, [])]


def blit_text(
    surface: pygame.Surface, text: str, position: tuple[int, int], color: tuple,
    font: pygame.font.Font, *, center: bool = False, right: bool = False,
) -> pygame.Rect:
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.midtop = position
    elif right:
        rect.topright = position
    else:
        rect.topleft = position
    surface.blit(rendered, rect)
    return rect


def draw_card(
    surface: pygame.Surface, rect: pygame.Rect, *,
    fill: tuple | None = None, accent: tuple | None = None, radius: int = CARD_RADIUS,
) -> None:
    shadow = pygame.Rect(rect.x, rect.y + CARD_SHADOW_OFFSET, rect.w, rect.h)
    pygame.draw.rect(surface, COLORS["shadow"], shadow, border_radius=radius)
    pygame.draw.rect(surface, fill or COLORS["panel"], rect, border_radius=radius)
    pygame.draw.rect(surface, COLORS["panel_border"], rect, width=1, border_radius=radius)
    if accent is not None:
        accent_bar = pygame.Rect(rect.x, rect.y, rect.w, CARD_ACCENT_HEIGHT)
        pygame.draw.rect(
            surface, accent, accent_bar,
            border_top_left_radius=radius, border_top_right_radius=radius,
            border_bottom_left_radius=0, border_bottom_right_radius=0,
        )


def _luminance(color: tuple) -> float:
    return 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]


def _pip_color(background: tuple) -> tuple:
    return (26, 28, 36) if _luminance(background) > 150 else (240, 242, 248)


def draw_die(
    surface: pygame.Surface, rect: pygame.Rect, color_name: str, value: int | None,
    *, available: bool = True, pulse: float = 0.0,
) -> None:
    background = DICE_COLORS.get(color_name, (180, 180, 185))
    if not available:
        background = dim(background, 90)

    shadow = pygame.Rect(rect.x, rect.y + 3, rect.w, rect.h)
    pygame.draw.rect(surface, COLORS["shadow"], shadow, border_radius=DIE_RADIUS)
    pygame.draw.rect(surface, background, rect, border_radius=DIE_RADIUS)

    if value is None:
        _center_glyph(surface, "?", rect, background)
    else:
        _draw_pips(surface, rect, value, _pip_color(background))

    if pulse > 0.0:
        glow = pygame.Rect(rect.x - 2, rect.y - 2, rect.w + 4, rect.h + 4)
        width = max(2, round(4 * pulse))
        pygame.draw.rect(surface, COLORS["prompt"], glow, width=width, border_radius=DIE_RADIUS + 2)


def _center_glyph(surface: pygame.Surface, text: str, rect: pygame.Rect, background: tuple) -> None:
    font = pygame.font.Font(None, int(rect.h * 0.72))
    rendered = font.render(text, True, _pip_color(background))
    surface.blit(rendered, rendered.get_rect(center=rect.center))


def _draw_pips(surface: pygame.Surface, rect: pygame.Rect, value: int, color: tuple) -> None:
    radius = max(2, round(rect.w * PIP_RADIUS_RATIO))
    for fraction_x, fraction_y in pip_offsets(value):
        center = (round(rect.x + fraction_x * rect.w), round(rect.y + fraction_y * rect.h))
        pygame.draw.circle(surface, color, center, radius)


def draw_button(
    surface: pygame.Surface, rect: pygame.Rect, label: str, font: pygame.font.Font,
    *, state: str = "normal", is_hint: bool = False,
) -> None:
    fill = {
        "hover": COLORS["button_hover"],
        "press": COLORS["button_press"],
    }.get(state, COLORS["button"])
    shadow = pygame.Rect(rect.x, rect.y + 3, rect.w, rect.h)
    pygame.draw.rect(surface, COLORS["shadow"], shadow, border_radius=BUTTON_RADIUS)
    pygame.draw.rect(surface, fill, rect, border_radius=BUTTON_RADIUS)
    if is_hint:
        pygame.draw.rect(surface, COLORS["button_hint"], rect, width=3, border_radius=BUTTON_RADIUS)
    rendered = font.render(label, True, COLORS["button_text"])
    surface.blit(rendered, rendered.get_rect(center=rect.center))


def draw_pill(
    surface: pygame.Surface, position: tuple[int, int], text: str,
    font: pygame.font.Font, color: tuple, height: int,
) -> int:
    rendered = font.render(text, True, color)
    width = rendered.get_width() + 14
    rect = pygame.Rect(position[0], position[1], width, height)
    pygame.draw.rect(surface, dim(color, 150), rect, border_radius=PILL_RADIUS)
    pygame.draw.rect(surface, color, rect, width=1, border_radius=PILL_RADIUS)
    surface.blit(rendered, rendered.get_rect(center=rect.center))
    return width
