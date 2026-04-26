# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
from __future__ import annotations

from typing import Any

import pygame

from src.ui.constants import COLORS, DICE_COLORS
from src.ui.render_snapshot import RenderSnapshot


class Renderer:  # pylint: disable=too-few-public-methods

    def __init__(
        self,
        screen: pygame.Surface,
        font_regular: pygame.font.Font,
        font_small: pygame.font.Font,
        font_large: pygame.font.Font,
    ) -> None:
        self._screen = screen
        self._font_regular = font_regular
        self._font_small = font_small
        self._font_large = font_large

    def render(self, snapshot: RenderSnapshot) -> list[pygame.Rect]:
        self._screen.fill(COLORS["background"])
        screen_width, screen_height = self._screen.get_size()

        vertical_offset = self._render_title(snapshot.round_number, screen_width, vertical_offset=10)
        vertical_offset = self._render_dice_row(snapshot.dice, snapshot.available_dice, screen_width, vertical_offset)
        vertical_offset += 10

        panel_width, panel_height = self._calculate_panel_dimensions(screen_width, screen_height, vertical_offset)
        self._render_board_panels(snapshot.board_data, vertical_offset, panel_width, panel_height)

        status_vertical_offset = vertical_offset + 2 * (panel_height + 15) + 5
        status_vertical_offset = self._render_status_bar(snapshot.board_data, screen_width, status_vertical_offset)

        if snapshot.is_game_over and snapshot.score is not None:
            status_vertical_offset = self._render_game_over_banner(snapshot.score, screen_width, status_vertical_offset)

        button_rects: list[pygame.Rect] = []
        if snapshot.is_waiting and snapshot.options:
            button_rects = self._render_prompt_with_buttons(
                snapshot.prompt,
                snapshot.options,
                screen_width,
                status_vertical_offset,
            )

        pygame.display.flip()
        return button_rects

    def _render_title(self, round_number: int, screen_width: int, vertical_offset: int) -> int:
        title = f"Doppelt So Clever  —  Round {round_number}"
        self._draw_text(title, (screen_width // 2, vertical_offset), COLORS["text"], self._font_large, center_x=True)
        return vertical_offset + 40

    def _render_dice_row(self, dice: list, available_dice: list, screen_width: int, vertical_offset: int) -> int:
        if not dice:
            return vertical_offset
        die_size = 52
        gap = 14
        total_width = len(dice) * die_size + (len(dice) - 1) * gap
        start_x = (screen_width - total_width) // 2
        available_ids = set(id(die) for die in available_dice)

        for index, die in enumerate(dice):
            die_x = start_x + index * (die_size + gap)
            self._render_single_die(die, die_x, vertical_offset, die_size, die in available_dice or id(die) in available_ids)

        return vertical_offset + die_size + 6

    def _render_single_die(self, die: Any, x_position: int, y_position: int, size: int, is_available: bool) -> None:
        color_name = die.color.value if die.color else "white"
        background = DICE_COLORS.get(color_name, (180, 180, 180))
        if not is_available:
            background = tuple(max(channel - 80, 30) for channel in background)

        rect = pygame.Rect(x_position, y_position, size, size)
        pygame.draw.rect(self._screen, background, rect, border_radius=8)

        value_text = str(die.value) if die.value is not None else "?"
        text_color = (20, 20, 20) if color_name in ("white", "yellow") else (240, 240, 240)
        self._draw_text(value_text, (x_position + size // 2, y_position + 10), text_color, self._font_large, center_x=True)

    def _calculate_panel_dimensions(self, screen_width: int, screen_height: int, vertical_offset: int) -> tuple[int, int]:
        panel_width = (screen_width - 60) // 3
        panel_height = (screen_height - vertical_offset - 180) // 2
        panel_height = max(panel_height, 80)
        return panel_width, panel_height

    def _render_board_panels(self, board_data: dict, vertical_offset: int, panel_width: int, panel_height: int) -> None:
        panels = [
            ("YELLOW", self._render_yellow_panel, board_data["yellow"]),
            ("BLUE",   self._render_blue_panel,   board_data["blue"]),
            ("GREEN",  self._render_green_panel,  board_data["green"]),
            ("PINK",   self._render_pink_panel,   board_data["pink"]),
            ("GREY",   self._render_grey_panel,   board_data["grey"]),
        ]

        for index, (name, draw_function, data) in enumerate(panels):
            column = index % 3
            row = index // 3
            panel_x = 10 + column * (panel_width + 15)
            panel_y = vertical_offset + row * (panel_height + 15)
            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            pygame.draw.rect(self._screen, COLORS["panel"], panel_rect, border_radius=6)
            self._draw_text(name, (panel_x + 8, panel_y + 4), COLORS["dimmed"], self._font_small)
            draw_function(data, panel_rect)

    def _render_status_bar(self, board_data: dict, screen_width: int, vertical_offset: int) -> int:
        items = [
            f"Foxes: {board_data['foxes']}",
            f"Rerolls: {board_data['rerolls']['usable']}/{board_data['rerolls']['gained']}",
            f"Reuses: {board_data['reuses']['usable']}/{board_data['reuses']['gained']}",
            f"+1s: {board_data['plus_ones']['usable']}/{board_data['plus_ones']['gained']}",
        ]
        status_text = "   |   ".join(items)
        self._draw_text(
            status_text,
            (screen_width // 2, vertical_offset),
            COLORS["dimmed"],
            self._font_regular,
            center_x=True,
        )
        return vertical_offset + 28

    def _render_game_over_banner(self, score: int, screen_width: int, vertical_offset: int) -> int:
        self._draw_text(
            f"GAME OVER  —  Score: {score}",
            (screen_width // 2, vertical_offset),
            COLORS["score"],
            self._font_large,
            center_x=True,
        )
        return vertical_offset + 36

    def _render_prompt_with_buttons(
        self, prompt: str, options: list, screen_width: int, vertical_offset: int,
    ) -> list[pygame.Rect]:
        self._draw_text(
            prompt,
            (screen_width // 2, vertical_offset),
            COLORS["prompt"],
            self._font_regular,
            center_x=True,
        )
        vertical_offset += 28

        button_height = 36
        button_gap = 10
        max_button_width = 320
        button_width = min(max_button_width, (screen_width - 40) // max(len(options), 1) - button_gap)
        total_width = len(options) * button_width + (len(options) - 1) * button_gap
        start_x = (screen_width - total_width) // 2

        mouse_position = pygame.mouse.get_pos()
        button_rects: list[pygame.Rect] = []

        for index, option in enumerate(options):
            button_x = start_x + index * (button_width + button_gap)
            button_rect = pygame.Rect(button_x, vertical_offset, button_width, button_height)
            is_hovered = button_rect.collidepoint(mouse_position)
            background = COLORS["button_hover"] if is_hovered else COLORS["button"]
            pygame.draw.rect(self._screen, background, button_rect, border_radius=5)
            label = f"[{index}] {option}"
            self._draw_text(
                label,
                (button_x + button_width // 2, vertical_offset + 6),
                COLORS["button_text"],
                self._font_small,
                center_x=True,
            )
            button_rects.append(button_rect)

        return button_rects

    def _draw_text(
        self, text: str, position: tuple[int, int], colour: tuple, font: pygame.font.Font | None = None,
        *, center_x: bool = False,
    ) -> None:
        font = font or self._font_regular
        surface = font.render(text, True, colour)
        text_rect = surface.get_rect()
        if center_x:
            text_rect.midtop = position  # type: ignore[assignment]
        else:
            text_rect.topleft = position  # type: ignore[assignment]
        self._screen.blit(surface, text_rect)

    def _render_yellow_panel(self, data: list[dict], panel: pygame.Rect) -> None:
        grid: dict[tuple[int, int], dict] = {}
        for box in data:
            grid[(box["row"], box["col"])] = box
        box_size = min((panel.w - 20) // 4, (panel.h - 30) // 5, 32)
        origin_x = panel.x + (panel.w - 4 * (box_size + 4)) // 2
        origin_y = panel.y + 22

        for row in range(5):
            for column in range(4):
                self._render_yellow_cell(grid, row, column, origin_x, origin_y, box_size)

    def _render_yellow_cell(
        self, grid: dict[tuple[int, int], dict], row: int, column: int,
        origin_x: int, origin_y: int, box_size: int,
    ) -> None:
        box_x = origin_x + column * (box_size + 4)
        box_y = origin_y + row * (box_size + 4)
        rect = pygame.Rect(box_x, box_y, box_size, box_size)
        box = grid.get((row, column))

        if box is None:
            pygame.draw.rect(self._screen, COLORS["background"], rect, border_radius=3)
            return

        background = self._get_yellow_box_color(box)
        pygame.draw.rect(self._screen, background, rect, border_radius=3)
        self._draw_text(str(box["value"]), (box_x + box_size // 2, box_y + 2), (20, 20, 20), self._font_small, center_x=True)

    @staticmethod
    def _get_yellow_box_color(box: dict) -> tuple:
        if box["crossed"]:
            return COLORS["crossed"]
        if box["circled"]:
            return COLORS["circled"]
        return COLORS["yellow"]

    def _render_blue_panel(self, data: list[dict], panel: pygame.Rect) -> None:
        count = len(data)
        box_width = min((panel.w - 20) // count, 30)
        origin_x = panel.x + 8
        origin_y = panel.y + 24

        for index, box in enumerate(data):
            box_x = origin_x + index * (box_width + 3)
            rect = pygame.Rect(box_x, origin_y, box_width, box_width)
            background = COLORS["blue"] if box["value_used"] is not None else COLORS["box_empty"]
            pygame.draw.rect(self._screen, background, rect, border_radius=3)
            label = str(box["value_used"]) if box["value_used"] is not None else f"≤{box['max_limit']}"
            self._draw_text(label, (box_x + box_width // 2, origin_y + 2), COLORS["text"], self._font_small, center_x=True)

    def _render_green_panel(self, data: list[dict], panel: pygame.Rect) -> None:
        count = len(data)
        box_width = min((panel.w - 20) // count, 30)
        origin_x = panel.x + 8
        origin_y = panel.y + 24

        for index, box in enumerate(data):
            box_x = origin_x + index * (box_width + 3)
            rect = pygame.Rect(box_x, origin_y, box_width, box_width)
            background = COLORS["green"] if box["value_used"] is not None else COLORS["box_empty"]
            pygame.draw.rect(self._screen, background, rect, border_radius=3)
            label = self._get_green_box_label(box, index)
            self._draw_text(label, (box_x + box_width // 2, origin_y + 2), COLORS["text"], self._font_small, center_x=True)

    @staticmethod
    def _get_green_box_label(box: dict, index: int) -> str:
        if box["value_used"] is not None:
            return str(box["value_used"])
        sign = "+" if index % 2 == 0 else "-"
        return f"{sign}{box['multiplier']}x"

    def _render_pink_panel(self, data: list[dict], panel: pygame.Rect) -> None:
        count = len(data)
        box_width = min((panel.w - 20) // count, 30)
        origin_x = panel.x + 8
        origin_y = panel.y + 24

        for index, box in enumerate(data):
            box_x = origin_x + index * (box_width + 3)
            rect = pygame.Rect(box_x, origin_y, box_width, box_width)
            background = COLORS["pink"] if box["value_used"] is not None else COLORS["box_empty"]
            pygame.draw.rect(self._screen, background, rect, border_radius=3)
            label = self._get_pink_box_label(box)
            self._draw_text(label, (box_x + box_width // 2, origin_y + 2), COLORS["text"], self._font_small, center_x=True)

    @staticmethod
    def _get_pink_box_label(box: dict) -> str:
        if box["value_used"] is not None:
            return str(box["value_used"])
        if box["filter_limit"]:
            return f"≥{box['filter_limit']}"
        return "—"

    def _render_grey_panel(self, data: list[dict], panel: pygame.Rect) -> None:
        color_names = ["yellow", "blue", "green", "pink"]
        rows_by_color: dict[str, list[dict]] = {color: [] for color in color_names}
        for box in data:
            rows_by_color[box["color"]].append(box)

        box_size = min((panel.w - 20) // 6, (panel.h - 30) // 4, 26)
        origin_x = panel.x + 8
        origin_y = panel.y + 22

        for row_index, color_name in enumerate(color_names):
            sorted_boxes = sorted(rows_by_color[color_name], key=lambda box: box["number"])
            for column_index, box in enumerate(sorted_boxes):
                self._render_grey_cell(box, color_name, origin_x, origin_y, row_index, column_index, box_size)

    def _render_grey_cell(
        self, box: dict, color_name: str,
        origin_x: int, origin_y: int, row_index: int, column_index: int, box_size: int,
    ) -> None:
        box_x = origin_x + column_index * (box_size + 3)
        box_y = origin_y + row_index * (box_size + 3)
        rect = pygame.Rect(box_x, box_y, box_size, box_size)

        if box["crossed"]:
            background = COLORS["crossed"]
        else:
            base_color = DICE_COLORS.get(color_name, COLORS["box_empty"])
            background = tuple(max(channel - 40, 20) for channel in base_color)

        pygame.draw.rect(self._screen, background, rect, border_radius=2)
        self._draw_text(
            str(box["number"]),
            (box_x + box_size // 2, box_y + 1),
            COLORS["text"],
            self._font_small,
            center_x=True,
        )
