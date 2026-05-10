# pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
from __future__ import annotations

from typing import Any

import pygame

from src.board.board_types import (
    BoardDict, BlueBoxDict, GreenBoxDict, PinkBoxDict,
    YellowBoxDict, GreyBoxDict, PositionalActionDict,
)
from src.ui.constants import (
    COLORS, DICE_COLORS, ACTION_LABELS, ACTION_LABEL_COLORS,
    TITLE_TOP_MARGIN, TITLE_SECTION_HEIGHT, PANEL_LEFT_MARGIN, PANEL_GAP,
    PANEL_TOTAL_HORIZONTAL_MARGIN, PANEL_BOTTOM_RESERVE, PANEL_MIN_HEIGHT,
    STATUS_BAR_TOP_MARGIN, PANEL_PADDING_X, PANEL_HEADER_OFFSET_Y,
    PANEL_CONTENT_OFFSET_Y, PANEL_BORDER_RADIUS, BOX_BORDER_RADIUS,
    GREY_BOX_BORDER_RADIUS, BUTTON_BORDER_RADIUS, DIE_BORDER_RADIUS,
    PILL_BORDER_RADIUS, DIE_SIZE, DIE_GAP, DIE_SECTION_LABEL_OFFSET_Y,
    DIE_SECTION_BOTTOM_PADDING, DIE_TEXT_OFFSET_Y, BOX_ROW_MAX_SIZE,
    BOX_ROW_GAP, BOX_ROW_CONTENT_OFFSET_Y, BOX_ROW_MARGIN,
    BOX_ROW_TEXT_OFFSET_Y, BOX_ROW_ACTION_OFFSET_Y, YELLOW_GRID_GAP,
    YELLOW_GRID_COLS, YELLOW_GRID_ROWS, YELLOW_GRID_MARGIN_H,
    YELLOW_GRID_MARGIN_V, YELLOW_GRID_ACTION_MARGIN,
    YELLOW_ROW_ACTION_X_OFFSET, YELLOW_ACTION_Y_OFFSET,
    YELLOW_CELL_TEXT_OFFSET_Y, GREY_BOX_GAP, GREY_GRID_COLS, GREY_GRID_ROWS,
    GREY_GRID_MARGIN_H, GREY_GRID_MARGIN_V, GREY_ACTION_Y_OFFSET,
    GREY_CELL_TEXT_OFFSET_Y, PILL_HEIGHT, PILL_GAP, PILL_TEXT_PADDING,
    PILL_TEXT_OFFSET_X, PILL_TEXT_OFFSET_Y, PILL_BOTTOM_MARGIN,
    WON_ACTIONS_EMPTY_OFFSET_Y, BUTTON_HEIGHT, BUTTON_GAP, BUTTON_MAX_WIDTH,
    BUTTON_AREA_MARGIN, BUTTON_TEXT_OFFSET_Y, BUTTON_HINT_BORDER_WIDTH,
    STATUS_BAR_HEIGHT,
    PROMPT_TEXT_HEIGHT, GAME_OVER_BANNER_HEIGHT, SCORE_RATING_HEIGHT,
    POPUP_WIDTH, POPUP_HEIGHT, POPUP_GAP, POPUP_MARGIN_RIGHT,
    POPUP_MARGIN_TOP, POPUP_BORDER_RADIUS, POPUP_TEXT_OFFSET_X,
    POPUP_TEXT_OFFSET_Y, POPUP_ACTION_NAMES, POPUP_SOURCE_NAMES,
)
from src.game.score_rating import get_score_rating
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

        vertical_offset = self._render_title(
            snapshot.round_number, snapshot.is_active_round, snapshot.subround,
            screen_width, vertical_offset=TITLE_TOP_MARGIN,
        )

        panel_width, panel_height = self._calculate_panel_dimensions(screen_width, screen_height, vertical_offset)
        self._render_board_panels(snapshot, vertical_offset, panel_width, panel_height)

        status_vertical_offset = vertical_offset + 2 * (panel_height + PANEL_GAP) + STATUS_BAR_TOP_MARGIN
        status_vertical_offset = self._render_status_bar(
            snapshot.board_data,
            snapshot.score,
            screen_width,
            status_vertical_offset,
        )

        if snapshot.is_game_over and snapshot.score is not None:
            status_vertical_offset = self._render_game_over_banner(snapshot.score, screen_width, status_vertical_offset)

        button_rects: list[pygame.Rect] = []
        if snapshot.is_waiting and snapshot.options:
            button_rects = self._render_prompt_with_buttons(
                snapshot.prompt,
                snapshot.options,
                screen_width,
                status_vertical_offset,
                snapshot.hint_index,
            )

        if snapshot.popup_notifications:
            self._render_popups(snapshot.popup_notifications, screen_width)

        pygame.display.flip()
        return button_rects

    def _render_title(
        self, round_number: int, is_active_round: bool, subround: int,
        screen_width: int, vertical_offset: int,
    ) -> int:
        round_type = "Active" if is_active_round else "Passive"
        title = f"Doppelt So Clever  —  Round {round_number}  [{round_type}"
        if is_active_round and subround > 0:
            title += f" #{subround}"
        title += "]"
        self._draw_text(title, (screen_width // 2, vertical_offset), COLORS["text"], self._font_large, center_x=True)
        return vertical_offset + TITLE_SECTION_HEIGHT

    def _render_dice_panel(self, snapshot: RenderSnapshot, panel: pygame.Rect) -> None:
        pygame.draw.rect(self._screen, COLORS["panel"], panel, border_radius=PANEL_BORDER_RADIUS)
        self._draw_text(
            "DICE",
            (panel.x + PANEL_PADDING_X, panel.y + PANEL_HEADER_OFFSET_Y),
            COLORS["dimmed"],
            self._font_small,
        )
        y_offset = panel.y + PANEL_CONTENT_OFFSET_Y
        y_offset = self._render_dice_section(
            "Remaining", snapshot.dice, snapshot.available_dice,
            panel.x, panel.w, y_offset, dim_unavailable=True,
        )
        if snapshot.picked_dice:
            y_offset = self._render_dice_section(
                "Chosen", snapshot.picked_dice, snapshot.picked_dice,
                panel.x, panel.w, y_offset, dim_unavailable=False,
            )
        if snapshot.discarded_dice:
            self._render_dice_section(
                "Discarded", snapshot.discarded_dice, [],
                panel.x, panel.w, y_offset, dim_unavailable=True,
            )

    def _render_dice_section(
        self, label: str, dice: list, highlighted_dice: list,
        area_x: int, area_width: int, vertical_offset: int, *, dim_unavailable: bool,
    ) -> int:
        if not dice:
            return vertical_offset
        self._draw_text(
            label,
            (area_x + PANEL_PADDING_X, vertical_offset + DIE_SECTION_LABEL_OFFSET_Y),
            COLORS["dimmed"],
            self._font_small,
        )
        total_width = len(dice) * DIE_SIZE + (len(dice) - 1) * DIE_GAP
        start_x = area_x + (area_width - total_width) // 2
        for index, die in enumerate(dice):
            die_x = start_x + index * (DIE_SIZE + DIE_GAP)
            is_highlighted = any(die is h for h in highlighted_dice)
            self._render_single_die(die, die_x, vertical_offset, DIE_SIZE, is_highlighted or not dim_unavailable)

        return vertical_offset + DIE_SIZE + DIE_SECTION_BOTTOM_PADDING

    def _render_single_die(self, die: Any, x_position: int, y_position: int, size: int, is_available: bool) -> None:
        color_name = die.color.value if die.color else "white"
        background = DICE_COLORS.get(color_name, (180, 180, 180))
        if not is_available:
            background = tuple(max(channel - 80, 30) for channel in background)

        rect = pygame.Rect(x_position, y_position, size, size)
        pygame.draw.rect(self._screen, background, rect, border_radius=DIE_BORDER_RADIUS)

        value_text = str(die.value) if die.value is not None else "?"
        text_color = (20, 20, 20) if color_name in ("white", "yellow") else (240, 240, 240)
        self._draw_text(
            value_text,
            (x_position + size // 2, y_position + DIE_TEXT_OFFSET_Y),
            text_color,
            self._font_large,
            center_x=True,
        )

    def _calculate_panel_dimensions(self, screen_width: int, screen_height: int, vertical_offset: int) -> tuple[int, int]:
        panel_width = (screen_width - PANEL_TOTAL_HORIZONTAL_MARGIN) // 3
        panel_height = (screen_height - vertical_offset - PANEL_BOTTOM_RESERVE) // 2
        panel_height = max(panel_height, PANEL_MIN_HEIGHT)
        return panel_width, panel_height

    def _render_board_panels(
        self, snapshot: RenderSnapshot, vertical_offset: int, panel_width: int, panel_height: int,
    ) -> None:
        board_data = snapshot.board_data
        panels = [
            ("YELLOW", self._render_yellow_panel, {
                "boxes": board_data["yellow"],
                "row_actions": board_data["yellow_row_actions"],
                "col_actions": board_data["yellow_col_actions"],
            }),
            (None, self._render_combined_panel, {
                "green": board_data["green"],
                "blue": board_data["blue"],
                "pink": board_data["pink"],
            }),
            ("GREY", self._render_grey_panel, {
                "boxes": board_data["grey"],
                "col_actions": board_data["grey_col_actions"],
            }),
        ]

        for index, (name, draw_function, data) in enumerate(panels):
            panel_x = PANEL_LEFT_MARGIN + index * (panel_width + PANEL_GAP)
            panel_y = vertical_offset
            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            pygame.draw.rect(self._screen, COLORS["panel"], panel_rect, border_radius=PANEL_BORDER_RADIUS)
            if name:
                self._draw_text(
                    name,
                    (panel_x + PANEL_PADDING_X, panel_y + PANEL_HEADER_OFFSET_Y),
                    COLORS["dimmed"],
                    self._font_small,
                )
            draw_function(data, panel_rect)

        second_row_y = vertical_offset + (panel_height + PANEL_GAP)

        won_actions_width = 2 * panel_width + PANEL_GAP
        won_actions_rect = pygame.Rect(PANEL_LEFT_MARGIN, second_row_y, won_actions_width, panel_height)
        self._render_won_actions_panel(snapshot.won_actions, won_actions_rect)

        dice_panel_x = PANEL_LEFT_MARGIN + 2 * (panel_width + PANEL_GAP)
        dice_panel_rect = pygame.Rect(dice_panel_x, second_row_y, panel_width, panel_height)
        self._render_dice_panel(snapshot, dice_panel_rect)

    def _render_status_bar(self, board_data: BoardDict, score: int | None, screen_width: int, vertical_offset: int) -> int:
        segments = [
            (f"Score: {score if score is not None else '-'}", COLORS["score"]),
            (f"Foxes ({ACTION_LABELS['fox']}): {board_data['foxes']}", ACTION_LABEL_COLORS["fox"]),
            (f"Rerolls ({ACTION_LABELS['reroll']}): {board_data['rerolls']['usable']}/{board_data['rerolls']['gained']}",
             ACTION_LABEL_COLORS["reroll"]),
            (f"Reuses ({ACTION_LABELS['reuse']}): {board_data['reuses']['usable']}/{board_data['reuses']['gained']}",
             ACTION_LABEL_COLORS["reuse"]),
            (f"+1s ({ACTION_LABELS['plus_one']}): {board_data['plus_ones']['usable']}/{board_data['plus_ones']['gained']}",
             ACTION_LABEL_COLORS["plus_one"]),
        ]
        separator = "   |   "
        surfaces = [(self._font_regular.render(text, True, color), color) for text, color in segments]
        sep_surface = self._font_regular.render(separator, True, COLORS["dimmed"])
        total_width = sum(s.get_width() for s, _ in surfaces) + sep_surface.get_width() * (len(surfaces) - 1)
        x_position = (screen_width - total_width) // 2

        for index, (surface, _) in enumerate(surfaces):
            self._screen.blit(surface, (x_position, vertical_offset))
            x_position += surface.get_width()
            if index < len(surfaces) - 1:
                self._screen.blit(sep_surface, (x_position, vertical_offset))
                x_position += sep_surface.get_width()

        return vertical_offset + STATUS_BAR_HEIGHT

    def _render_game_over_banner(self, score: int, screen_width: int, vertical_offset: int) -> int:
        rating = get_score_rating(score)
        self._draw_text(
            f"GAME OVER  —  Score: {score}",
            (screen_width // 2, vertical_offset),
            COLORS["score"],
            self._font_large,
            center_x=True,
        )
        if rating:
            self._draw_text(
                rating,
                (screen_width // 2, vertical_offset + GAME_OVER_BANNER_HEIGHT),
                COLORS["prompt"],
                self._font_regular,
                center_x=True,
            )
        return vertical_offset + GAME_OVER_BANNER_HEIGHT + SCORE_RATING_HEIGHT

    def _render_prompt_with_buttons(
        self, prompt: str, options: list, screen_width: int, vertical_offset: int,
        hint_index: int | None = None,
    ) -> list[pygame.Rect]:
        hint_label = "  [H] Ask model" if hint_index is None else ""
        self._draw_text(
            prompt + hint_label,
            (screen_width // 2, vertical_offset),
            COLORS["prompt"],
            self._font_regular,
            center_x=True,
        )
        vertical_offset += PROMPT_TEXT_HEIGHT

        button_width = min(BUTTON_MAX_WIDTH, (screen_width - BUTTON_AREA_MARGIN) // max(len(options), 1) - BUTTON_GAP)
        total_width = len(options) * button_width + (len(options) - 1) * BUTTON_GAP
        start_x = (screen_width - total_width) // 2

        mouse_position = pygame.mouse.get_pos()
        button_rects: list[pygame.Rect] = []

        for index, option in enumerate(options):
            button_x = start_x + index * (button_width + BUTTON_GAP)
            button_rect = pygame.Rect(button_x, vertical_offset, button_width, BUTTON_HEIGHT)
            is_hovered = button_rect.collidepoint(mouse_position)
            background = COLORS["button_hover"] if is_hovered else COLORS["button"]
            pygame.draw.rect(self._screen, background, button_rect, border_radius=BUTTON_BORDER_RADIUS)
            if hint_index == index:
                pygame.draw.rect(
                    self._screen, COLORS["button_hint"], button_rect,
                    width=BUTTON_HINT_BORDER_WIDTH, border_radius=BUTTON_BORDER_RADIUS,
                )
            label = f"[{index}] {option}"
            self._draw_text(
                label,
                (button_x + button_width // 2, vertical_offset + BUTTON_TEXT_OFFSET_Y),
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

    def _render_action_label(self, action: str, center_x: int, y_position: int) -> None:
        label = ACTION_LABELS.get(action, "")
        if not label:
            return
        color = ACTION_LABEL_COLORS.get(action, COLORS["dimmed"])
        self._draw_text(label, (center_x, y_position), color, self._font_small, center_x=True)

    def _render_yellow_panel(self, data: dict, panel: pygame.Rect) -> None:
        grid: dict[tuple[int, int], YellowBoxDict] = {}
        for box in data["boxes"]:
            grid[(box["row"], box["col"])] = box
        box_size = min(
            (panel.w - YELLOW_GRID_MARGIN_H) // YELLOW_GRID_COLS,
            (panel.h - YELLOW_GRID_MARGIN_V) // YELLOW_GRID_ROWS,
        )
        grid_width = YELLOW_GRID_COLS * (box_size + YELLOW_GRID_GAP)
        origin_x = panel.x + (panel.w - grid_width - YELLOW_GRID_ACTION_MARGIN) // 2
        origin_y = panel.y + PANEL_CONTENT_OFFSET_Y

        for row in range(YELLOW_GRID_ROWS):
            for column in range(YELLOW_GRID_COLS):
                self._render_yellow_cell(grid, row, column, origin_x, origin_y, box_size)

        self._render_yellow_row_actions(data["row_actions"], origin_x, origin_y, grid_width, box_size)
        self._render_yellow_col_actions(data["col_actions"], origin_x, origin_y, box_size)

    def _render_yellow_row_actions(
        self, row_actions: dict, origin_x: int, origin_y: int, grid_width: int, box_size: int,
    ) -> None:
        for row in range(YELLOW_GRID_ROWS):
            action_info = row_actions.get(row, {})
            if not action_info:
                continue
            action_x = origin_x + grid_width + YELLOW_ROW_ACTION_X_OFFSET
            action_y = origin_y + row * (box_size + YELLOW_GRID_GAP) + YELLOW_ACTION_Y_OFFSET
            self._render_positional_action(action_info, action_x, action_y, center_x=False)

    def _render_yellow_col_actions(
        self, col_actions: dict, origin_x: int, origin_y: int, box_size: int,
    ) -> None:
        for column in range(YELLOW_GRID_COLS):
            action_info = col_actions.get(column, {})
            if not action_info:
                continue
            action_x = origin_x + column * (box_size + YELLOW_GRID_GAP) + box_size // 2
            action_y = origin_y + YELLOW_GRID_ROWS * (box_size + YELLOW_GRID_GAP) + YELLOW_ACTION_Y_OFFSET
            self._render_positional_action(action_info, action_x, action_y, center_x=True)

    def _render_positional_action(
        self, action_info: PositionalActionDict, x_position: int, y_position: int, *, center_x: bool,
    ) -> None:
        label = ACTION_LABELS.get(action_info["action"], "")
        if not label:
            return
        color = ACTION_LABEL_COLORS.get(action_info["action"], COLORS["dimmed"])
        if not action_info["available"]:
            color = tuple(max(c - 80, 40) for c in color)
        self._draw_text(label, (x_position, y_position), color, self._font_small, center_x=center_x)

    def _render_yellow_cell(
        self, grid: dict[tuple[int, int], YellowBoxDict], row: int, column: int,
        origin_x: int, origin_y: int, box_size: int,
    ) -> None:
        box_x = origin_x + column * (box_size + YELLOW_GRID_GAP)
        box_y = origin_y + row * (box_size + YELLOW_GRID_GAP)
        rect = pygame.Rect(box_x, box_y, box_size, box_size)
        box = grid.get((row, column))

        if box is None:
            pygame.draw.rect(self._screen, COLORS["background"], rect, border_radius=BOX_BORDER_RADIUS)
            return

        background = self._get_yellow_box_color(box)
        pygame.draw.rect(self._screen, background, rect, border_radius=BOX_BORDER_RADIUS)
        self._draw_text(
            str(box["value"]),
            (box_x + box_size // 2, box_y + YELLOW_CELL_TEXT_OFFSET_Y),
            (20, 20, 20),
            self._font_small,
            center_x=True,
        )

    @staticmethod
    def _get_yellow_box_color(box: YellowBoxDict) -> tuple:
        if box["crossed"]:
            return COLORS["crossed"]
        if box["circled"]:
            return COLORS["circled"]
        return COLORS["yellow"]

    def _render_combined_panel(self, data: dict, panel: pygame.Rect) -> None:
        sections = [
            ("GREEN", self._render_green_panel, data["green"]),
            ("BLUE", self._render_blue_panel, data["blue"]),
            ("PINK", self._render_pink_panel, data["pink"]),
        ]
        section_height = panel.h // len(sections)
        for i, (name, render_fn, section_data) in enumerate(sections):
            sub_y = panel.y + i * section_height
            sub_rect = pygame.Rect(panel.x, sub_y, panel.w, section_height)
            self._draw_text(
                name,
                (sub_rect.x + PANEL_PADDING_X, sub_y + PANEL_HEADER_OFFSET_Y),
                COLORS["dimmed"],
                self._font_small,
            )
            render_fn(section_data, sub_rect)

    def _render_blue_panel(self, data: list[BlueBoxDict], panel: pygame.Rect) -> None:
        count = len(data)
        box_width = min((panel.w - BOX_ROW_MARGIN) // count, BOX_ROW_MAX_SIZE)
        origin_x = panel.x + PANEL_PADDING_X
        origin_y = panel.y + BOX_ROW_CONTENT_OFFSET_Y

        for index, box in enumerate(data):
            box_x = origin_x + index * (box_width + BOX_ROW_GAP)
            rect = pygame.Rect(box_x, origin_y, box_width, box_width)
            background = COLORS["blue"] if box["value_used"] is not None else COLORS["box_empty"]
            pygame.draw.rect(self._screen, background, rect, border_radius=BOX_BORDER_RADIUS)
            label = str(box["value_used"]) if box["value_used"] is not None else f"≤{box['max_limit']}"
            self._draw_text(
                label,
                (box_x + box_width // 2, origin_y + BOX_ROW_TEXT_OFFSET_Y),
                COLORS["text"],
                self._font_small,
                center_x=True,
            )
            self._render_action_label(box["action"], box_x + box_width // 2, origin_y + box_width + BOX_ROW_ACTION_OFFSET_Y)

    def _render_green_panel(self, data: list[GreenBoxDict], panel: pygame.Rect) -> None:
        count = len(data)
        box_width = min((panel.w - BOX_ROW_MARGIN) // count, BOX_ROW_MAX_SIZE)
        origin_x = panel.x + PANEL_PADDING_X
        origin_y = panel.y + BOX_ROW_CONTENT_OFFSET_Y

        for index, box in enumerate(data):
            box_x = origin_x + index * (box_width + BOX_ROW_GAP)
            rect = pygame.Rect(box_x, origin_y, box_width, box_width)
            background = COLORS["green"] if box["value_used"] is not None else COLORS["box_empty"]
            pygame.draw.rect(self._screen, background, rect, border_radius=BOX_BORDER_RADIUS)
            label = self._get_green_box_label(box, index)
            self._draw_text(
                label,
                (box_x + box_width // 2, origin_y + BOX_ROW_TEXT_OFFSET_Y),
                COLORS["text"],
                self._font_small,
                center_x=True,
            )
            self._render_action_label(box["action"], box_x + box_width // 2, origin_y + box_width + BOX_ROW_ACTION_OFFSET_Y)

    @staticmethod
    def _get_green_box_label(box: GreenBoxDict, index: int) -> str:
        if box["value_used"] is not None:
            return str(box["value_used"])
        sign = "+" if index % 2 == 0 else "-"
        return f"{sign}{box['multiplier']}x"

    def _render_pink_panel(self, data: list[PinkBoxDict], panel: pygame.Rect) -> None:
        count = len(data)
        box_width = min((panel.w - BOX_ROW_MARGIN) // count, BOX_ROW_MAX_SIZE)
        origin_x = panel.x + PANEL_PADDING_X
        origin_y = panel.y + BOX_ROW_CONTENT_OFFSET_Y

        for index, box in enumerate(data):
            box_x = origin_x + index * (box_width + BOX_ROW_GAP)
            rect = pygame.Rect(box_x, origin_y, box_width, box_width)
            background = COLORS["pink"] if box["value_used"] is not None else COLORS["box_empty"]
            pygame.draw.rect(self._screen, background, rect, border_radius=BOX_BORDER_RADIUS)
            label = self._get_pink_box_label(box)
            self._draw_text(
                label,
                (box_x + box_width // 2, origin_y + BOX_ROW_TEXT_OFFSET_Y),
                COLORS["text"],
                self._font_small,
                center_x=True,
            )
            self._render_action_label(box["action"], box_x + box_width // 2, origin_y + box_width + BOX_ROW_ACTION_OFFSET_Y)

    @staticmethod
    def _get_pink_box_label(box: PinkBoxDict) -> str:
        if box["value_used"] is not None:
            return str(box["value_used"])
        if box["filter_limit"]:
            return f"≥{box['filter_limit']}"
        return "—"

    def _render_grey_panel(self, data: dict, panel: pygame.Rect) -> None:
        color_names = ["yellow", "blue", "green", "pink"]
        rows_by_color: dict[str, list[GreyBoxDict]] = {color: [] for color in color_names}
        for box in data["boxes"]:
            rows_by_color[box["color"]].append(box)
        col_actions = data["col_actions"]

        box_size = min((panel.w - GREY_GRID_MARGIN_H) // GREY_GRID_COLS, (panel.h - GREY_GRID_MARGIN_V) // GREY_GRID_ROWS)
        origin_x = panel.x + PANEL_PADDING_X
        origin_y = panel.y + PANEL_CONTENT_OFFSET_Y

        for row_index, color_name in enumerate(color_names):
            sorted_boxes = sorted(rows_by_color[color_name], key=lambda box: box["number"])
            for column_index, box in enumerate(sorted_boxes):
                self._render_grey_cell(box, color_name, origin_x, origin_y, row_index, column_index, box_size)

        action_y = origin_y + GREY_GRID_ROWS * (box_size + GREY_BOX_GAP) + GREY_ACTION_Y_OFFSET
        for number in range(1, GREY_GRID_COLS + 1):
            action_info = col_actions.get(number, {})
            if not action_info:
                continue
            action_x = origin_x + (number - 1) * (box_size + GREY_BOX_GAP) + box_size // 2
            self._render_positional_action(action_info, action_x, action_y, center_x=True)

    def _render_won_actions_panel(self, won_actions: list[dict], panel: pygame.Rect) -> None:
        pygame.draw.rect(self._screen, COLORS["panel"], panel, border_radius=PANEL_BORDER_RADIUS)
        self._draw_text(
            "WON ACTIONS",
            (panel.x + PANEL_PADDING_X, panel.y + PANEL_HEADER_OFFSET_Y),
            COLORS["dimmed"],
            self._font_small,
        )

        if not won_actions:
            self._draw_text(
                "No actions won yet",
                (panel.x + panel.w // 2, panel.y + panel.h // 2 - WON_ACTIONS_EMPTY_OFFSET_Y),
                COLORS["dimmed"], self._font_small, center_x=True,
            )
            return

        y_start = panel.y + PANEL_CONTENT_OFFSET_Y
        x_cursor = panel.x + PANEL_PADDING_X
        y_cursor = y_start
        max_x = panel.x + panel.w - PANEL_PADDING_X

        for entry in won_actions:
            action = entry["action"]
            label = ACTION_LABELS.get(action, action)
            if not label:
                continue
            color = ACTION_LABEL_COLORS.get(action, COLORS["dimmed"])
            text_surface = self._font_small.render(label, True, color)
            pill_width = text_surface.get_width() + PILL_TEXT_PADDING

            if x_cursor + pill_width > max_x:
                x_cursor = panel.x + PANEL_PADDING_X
                y_cursor += PILL_HEIGHT + PILL_GAP
                if y_cursor + PILL_HEIGHT > panel.y + panel.h - PILL_BOTTOM_MARGIN:
                    break

            pill_rect = pygame.Rect(x_cursor, y_cursor, pill_width, PILL_HEIGHT)
            bg = tuple(max(c // 4, 20) for c in color)
            pygame.draw.rect(self._screen, bg, pill_rect, border_radius=PILL_BORDER_RADIUS)
            pygame.draw.rect(self._screen, color, pill_rect, width=1, border_radius=PILL_BORDER_RADIUS)
            self._screen.blit(text_surface, (x_cursor + PILL_TEXT_OFFSET_X, y_cursor + PILL_TEXT_OFFSET_Y))
            x_cursor += pill_width + PILL_GAP

    def _render_popups(self, popups: list[dict], screen_width: int) -> None:
        x_position = screen_width - POPUP_WIDTH - POPUP_MARGIN_RIGHT
        y_position = POPUP_MARGIN_TOP

        for popup in popups:
            alpha = popup["alpha"]
            action = popup["action"]
            source = popup["source"]
            action_name = POPUP_ACTION_NAMES.get(action, action)
            source_name = POPUP_SOURCE_NAMES.get(source, source)
            color = ACTION_LABEL_COLORS.get(action, COLORS["dimmed"])

            bg_base = (70, 70, 90)
            bg = tuple(
                int(bg_base[i] * alpha + COLORS["background"][i] * (1 - alpha))
                for i in range(3)
            )
            border_color = tuple(
                int(c * alpha + COLORS["background"][i] * (1 - alpha))
                for i, c in enumerate(color)
            )
            text_color = tuple(
                int(240 * alpha + COLORS["background"][i] * (1 - alpha))
                for i in range(3)
            )

            popup_rect = pygame.Rect(x_position, y_position, POPUP_WIDTH, POPUP_HEIGHT)
            pygame.draw.rect(self._screen, bg, popup_rect, border_radius=POPUP_BORDER_RADIUS)
            pygame.draw.rect(self._screen, border_color, popup_rect, width=2, border_radius=POPUP_BORDER_RADIUS)

            text = f"Won {action_name}  ({source_name})"
            self._draw_text(
                text,
                (x_position + POPUP_TEXT_OFFSET_X, y_position + POPUP_TEXT_OFFSET_Y),
                text_color,
                self._font_regular,
            )

            y_position += POPUP_HEIGHT + POPUP_GAP

    def _render_grey_cell(
        self, box: GreyBoxDict, color_name: str,
        origin_x: int, origin_y: int, row_index: int, column_index: int, box_size: int,
    ) -> None:
        box_x = origin_x + column_index * (box_size + GREY_BOX_GAP)
        box_y = origin_y + row_index * (box_size + GREY_BOX_GAP)
        rect = pygame.Rect(box_x, box_y, box_size, box_size)

        if box["crossed"]:
            background = COLORS["crossed"]
        else:
            base_color = DICE_COLORS.get(color_name, COLORS["box_empty"])
            background = tuple(max(channel - 40, 20) for channel in base_color)

        pygame.draw.rect(self._screen, background, rect, border_radius=GREY_BOX_BORDER_RADIUS)
        self._draw_text(
            str(box["number"]),
            (box_x + box_size // 2, box_y + GREY_CELL_TEXT_OFFSET_Y),
            COLORS["text"],
            self._font_small,
            center_x=True,
        )
