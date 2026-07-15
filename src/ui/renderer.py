from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from src.board.board_types import (
    BoardDict, BlueBoxDict, GreenBoxDict, PinkBoxDict,
    YellowBoxDict, GreyBoxDict, PositionalActionDict,
)
from src.ui.theme import COLORS, SECTION_COLORS, ACTION_COLORS, Fonts, dim, mix
from src.ui.widgets import draw_card, draw_die, draw_button, draw_pill, blit_text
from src.ui.layout import Layout, POPUP_HEIGHT, POPUP_GAP, MAX_POPUPS
from src.ui.constants import ACTION_LABELS, POPUP_ACTION_NAMES, POPUP_SOURCE_NAMES
from src.ui.render_snapshot import RenderSnapshot
from src.game.score_rating import get_score_rating

PAD = 12
HEADER_Y = 8
CONTENT_Y = 30
DIE_SIZE = 42
DIE_GAP = 8
SECTION_GAP = 8
BUTTON_HEIGHT = 40
BUTTON_GAP = 12
BUTTON_MAX_WIDTH = 300
GRID_GAP = 4
BOX_RADIUS = 5
ROW_BOX_MAX = 38
CELL_TEXT_DARK = (24, 26, 34)

LEGEND = [
    ("R", "Reroll", "reroll"),
    ("U", "Reuse", "reuse"),
    ("+1", "Plus-one", "plus_one"),
    ("?", "Question", "black_question_mark"),
    ("F", "Fox", "fox"),
]


@dataclass
class RenderTargets:
    buttons: list[pygame.Rect] = field(default_factory=list)
    dice: list[tuple] = field(default_factory=list)


class Renderer:

    def __init__(self, screen: pygame.Surface, fonts: Fonts) -> None:
        self._screen = screen
        self._fonts = fonts
        self._scale = 1.0

    @property
    def screen(self) -> pygame.Surface:
        return self._screen

    @screen.setter
    def screen(self, value: pygame.Surface) -> None:
        self._screen = value

    @property
    def fonts(self) -> Fonts:
        return self._fonts

    @fonts.setter
    def fonts(self, value: Fonts) -> None:
        self._fonts = value

    def _px(self, value: int) -> int:
        return max(1, round(value * self._scale))

    def render(self, snapshot: RenderSnapshot, layout: Layout) -> RenderTargets:
        self._scale = layout.scale
        self._screen.fill(COLORS["background"])
        self._render_title(snapshot, layout)
        self._render_top_panels(snapshot, layout)
        self._render_won_actions(snapshot.won_actions, layout.won_actions)
        dice_targets = self._render_dice_panel(snapshot, layout.dice_panel)
        self._render_status_bar(snapshot, layout)

        buttons: list[pygame.Rect] = []
        if snapshot.is_game_over and snapshot.score is not None:
            self._render_game_over(snapshot.score, layout)
        elif snapshot.is_waiting and snapshot.options:
            buttons = self._render_prompt(snapshot, layout)

        self._render_popups(snapshot.popup_notifications, layout)
        if snapshot.show_help:
            self._render_help_overlay(layout)
        pygame.display.flip()
        return RenderTargets(buttons=buttons, dice=dice_targets)

    def _render_help_overlay(self, layout: Layout) -> None:
        veil = pygame.Surface((layout.width, layout.height), pygame.SRCALPHA)
        veil.fill((*COLORS["overlay"], 210))
        self._screen.blit(veil, (0, 0))

        lines = [
            ("Controls", COLORS["prompt"]),
            ("Click a highlighted die  —  pick it", COLORS["text"]),
            ("0 – 9  —  choose the numbered option", COLORS["text"]),
            ("H  —  ask the model for a hint", COLORS["text"]),
            ("F11  —  toggle fullscreen", COLORS["text"]),
            ("?  —  toggle this help", COLORS["text"]),
            ("Esc  —  quit", COLORS["dimmed"]),
        ]
        start_y = layout.height // 2 - len(lines) * 18
        for index, (text, color) in enumerate(lines):
            font = self._fonts.heading if index == 0 else self._fonts.body
            blit_text(self._screen, text, (layout.width // 2, start_y + index * 40), color, font, center=True)

    def _render_title(self, snapshot: RenderSnapshot, layout: Layout) -> None:
        round_type = "Active" if snapshot.is_active_round else "Passive"
        title = f"Doppelt So Clever   ·   Round {snapshot.round_number}   [{round_type}"
        if snapshot.is_active_round and snapshot.subround > 0:
            title += f" #{snapshot.subround}"
        title += "]"
        blit_text(self._screen, title, (layout.width // 2, layout.title_baseline),
                  COLORS["text"], self._fonts.heading, center=True)
        margin = self._px(18)
        pygame.draw.line(self._screen, COLORS["panel_border"],
                         (margin, layout.divider_y), (layout.width - margin, layout.divider_y))

    def _header(self, name: str, panel: pygame.Rect) -> None:
        blit_text(self._screen, name, (panel.x + self._px(PAD), panel.y + self._px(HEADER_Y)),
                  COLORS["dimmed"], self._fonts.label)

    def _render_top_panels(self, snapshot: RenderSnapshot, layout: Layout) -> None:
        board = snapshot.board_data
        yellow_rect, combined_rect, grey_rect = layout.top_panels

        draw_card(self._screen, yellow_rect, accent=SECTION_COLORS["yellow"])
        self._header("YELLOW", yellow_rect)
        self._render_yellow(board, yellow_rect)

        draw_card(self._screen, combined_rect)
        self._render_combined(board, combined_rect)

        draw_card(self._screen, grey_rect, accent=SECTION_COLORS["grey"])
        self._header("GREY", grey_rect)
        self._render_grey(board, grey_rect)

    def _render_status_bar(self, snapshot: RenderSnapshot, layout: Layout) -> None:
        board = snapshot.board_data
        score = snapshot.display_score if snapshot.display_score is not None else snapshot.score
        segments = [
            (f"Score {score if score is not None else '-'}", COLORS["score"]),
            (f"Foxes {board['foxes']}", ACTION_COLORS["fox"]),
            (f"Reroll {board['rerolls']['usable']}/{board['rerolls']['gained']}", ACTION_COLORS["reroll"]),
            (f"Reuse {board['reuses']['usable']}/{board['reuses']['gained']}", ACTION_COLORS["reuse"]),
            (f"+1 {board['plus_ones']['usable']}/{board['plus_ones']['gained']}", ACTION_COLORS["plus_one"]),
        ]
        gap = self._px(10)
        height = self._px(28)
        widths = [self._fonts.small.render(text, True, color).get_width() + self._px(20)
                  for text, color in segments]
        total = sum(widths) + gap * (len(segments) - 1)
        x_cursor = (layout.width - total) // 2
        for (text, color), width in zip(segments, widths):
            draw_pill(self._screen, (x_cursor, layout.status_y), text, self._fonts.small, color, height)
            x_cursor += width + gap

    def _render_game_over(self, score: int, layout: Layout) -> None:
        center_x = layout.width // 2
        blit_text(self._screen, f"GAME OVER   ·   Score {score}", (center_x, layout.prompt_y),
                  COLORS["score"], self._fonts.display, center=True)
        rating = get_score_rating(score)
        if rating:
            blit_text(self._screen, rating, (center_x, layout.prompt_y + self._px(44)),
                      COLORS["prompt"], self._fonts.body, center=True)

    def _render_prompt(self, snapshot: RenderSnapshot, layout: Layout) -> list[pygame.Rect]:
        hint = "     [H] ask model" if snapshot.hint_index is None else ""
        blit_text(self._screen, snapshot.prompt + hint, (layout.width // 2, layout.prompt_y),
                  COLORS["prompt"], self._fonts.body, center=True)

        count = len(snapshot.options)
        button_gap = self._px(BUTTON_GAP)
        button_y = layout.prompt_y + self._px(34)
        button_width = min(self._px(BUTTON_MAX_WIDTH),
                           (layout.width - 2 * self._px(PAD)) // max(count, 1) - button_gap)
        start_x = (layout.width - (count * button_width + (count - 1) * button_gap)) // 2
        mouse = pygame.mouse.get_pos()

        rects: list[pygame.Rect] = []
        for index, option in enumerate(snapshot.options):
            rect = pygame.Rect(start_x + index * (button_width + button_gap), button_y,
                               button_width, self._px(BUTTON_HEIGHT))
            draw_button(self._screen, rect, f"[{index}] {option}", self._fonts.small,
                        state=self._button_state(rect, index, snapshot.pressed_index, mouse),
                        is_hint=snapshot.hint_index == index)
            rects.append(rect)
        return rects

    @staticmethod
    def _button_state(rect: pygame.Rect, index: int, pressed_index: int | None, mouse: tuple) -> str:
        if pressed_index == index:
            return "press"
        return "hover" if rect.collidepoint(mouse) else "normal"

    def _render_dice_panel(self, snapshot: RenderSnapshot, panel: pygame.Rect) -> list[tuple]:
        draw_card(self._screen, panel)
        self._header("DICE", panel)
        die_size = self._dice_size(panel)
        targets: list[tuple] = []
        y_offset = panel.y + self._px(CONTENT_Y)
        rows = [
            ("Remaining", snapshot.dice, snapshot.available_dice),
            ("Chosen", snapshot.picked_dice, snapshot.picked_dice),
            ("Discarded", snapshot.discarded_dice, []),
        ]
        for label, dice, bright in rows:
            row_targets, y_offset = self._render_dice_row(label, dice, bright, snapshot, panel, y_offset, die_size)
            targets.extend(row_targets)
        return targets

    def _dice_size(self, panel: pygame.Rect) -> int:
        available = panel.h - self._px(CONTENT_Y) - self._px(8)
        row_height = available // 3
        fitted = row_height - self._px(16) - self._px(SECTION_GAP)
        return max(self._px(20), min(self._px(DIE_SIZE), fitted))

    def _render_dice_row(
        self, label: str, dice: list, bright: list, snapshot: RenderSnapshot,
        panel: pygame.Rect, y_offset: int, die_size: int,
    ) -> tuple[list[tuple], int]:
        blit_text(self._screen, label, (panel.x + self._px(PAD), y_offset), COLORS["muted"], self._fonts.tiny)
        row_y = y_offset + self._px(16)
        die_gap = self._px(DIE_GAP)
        start_x = panel.x + self._px(PAD)

        targets: list[tuple] = []
        for index, die in enumerate(dice):
            rect = pygame.Rect(start_x + index * (die_size + die_gap), row_y, die_size, die_size)
            if self._draw_die_cell(die, rect, bright, snapshot):
                targets.append((die, rect))
        return targets, row_y + die_size + self._px(SECTION_GAP)

    def _draw_die_cell(self, die, rect: pygame.Rect, bright: list, snapshot: RenderSnapshot) -> bool:
        is_bright = any(die is other for other in bright)
        selectable = id(die) in snapshot.selectable_die_ids
        color_name = die.color.value if die.color else "white"
        draw_die(self._screen, rect, color_name, die.value,
                 available=is_bright or selectable, pulse=snapshot.die_pulses.get(id(die), 0.0))
        if selectable:
            pygame.draw.rect(self._screen, COLORS["prompt"], rect.inflate(6, 6), width=2, border_radius=12)
        return selectable

    def _render_won_actions(self, won_actions: list[dict], panel: pygame.Rect) -> None:
        draw_card(self._screen, panel)
        self._header("WON ACTIONS", panel)
        self._render_won_pills(won_actions, panel)
        self._render_legend(panel)

    def _render_won_pills(self, won_actions: list[dict], panel: pygame.Rect) -> None:
        if not won_actions:
            blit_text(self._screen, "No actions won yet", (panel.x + self._px(PAD), panel.y + self._px(CONTENT_Y)),
                      COLORS["muted"], self._fonts.small)
            return
        x_cursor = panel.x + self._px(PAD)
        y_cursor = panel.y + self._px(CONTENT_Y)
        max_x = panel.right - self._px(PAD)
        pill_height = self._px(24)
        limit = panel.y + round(panel.h * 0.30)
        for entry in won_actions:
            label = ACTION_LABELS.get(entry["action"], entry["action"])
            if not label:
                continue
            color = ACTION_COLORS.get(entry["action"], COLORS["dimmed"])
            probe = self._fonts.small.render(label, True, color).get_width() + self._px(14)
            if x_cursor + probe > max_x:
                x_cursor = panel.x + self._px(PAD)
                y_cursor += pill_height + self._px(6)
                if y_cursor + pill_height > limit:
                    break
            width = draw_pill(self._screen, (x_cursor, y_cursor), label, self._fonts.small, color, pill_height)
            x_cursor += width + self._px(6)

    def _render_legend(self, panel: pygame.Rect) -> None:
        x_cursor = panel.x + self._px(PAD)
        y_position = panel.bottom - self._px(24)
        for glyph, name, action in LEGEND:
            glyph_rect = blit_text(self._screen, glyph, (x_cursor, y_position),
                                   ACTION_COLORS.get(action, COLORS["dimmed"]), self._fonts.label)
            name_rect = blit_text(self._screen, name, (glyph_rect.right + self._px(5), y_position),
                                  COLORS["muted"], self._fonts.tiny)
            x_cursor = name_rect.right + self._px(14)

    def _render_popups(self, popups: list[dict], layout: Layout) -> None:
        x_position, y_position = layout.popup_origin()
        width = layout.popup_width()
        step = self._px(POPUP_HEIGHT) + self._px(POPUP_GAP)
        for popup in popups[-MAX_POPUPS:]:
            self._draw_popup(pygame.Rect(x_position, y_position, width, self._px(POPUP_HEIGHT)), popup)
            y_position += step

    def _draw_popup(self, rect: pygame.Rect, popup: dict) -> None:
        alpha = popup["alpha"]
        color = ACTION_COLORS.get(popup["action"], COLORS["dimmed"])
        action_name = POPUP_ACTION_NAMES.get(popup["action"], popup["action"])
        source_name = POPUP_SOURCE_NAMES.get(popup["source"], popup["source"])
        pygame.draw.rect(self._screen, mix(COLORS["sunken"], COLORS["panel"], alpha), rect, border_radius=10)
        pygame.draw.rect(self._screen, mix(COLORS["sunken"], color, alpha), rect, width=2, border_radius=10)
        blit_text(self._screen, f"Won {action_name}   ({source_name})",
                  (rect.x + self._px(12), rect.centery - self._px(8)),
                  mix(COLORS["sunken"], COLORS["text"], alpha), self._fonts.small)

    def _render_action_label(self, action: str, center_x: int, y_position: int) -> None:
        label = ACTION_LABELS.get(action, "")
        if not label:
            return
        blit_text(self._screen, label, (center_x, y_position),
                  dim(ACTION_COLORS.get(action, COLORS["dimmed"]), 30), self._fonts.tiny, center=True)

    def _render_positional_action(
        self, action_info: PositionalActionDict, x_position: int, y_position: int, *, center: bool,
    ) -> None:
        label = ACTION_LABELS.get(action_info["action"], "")
        if not label:
            return
        color = ACTION_COLORS.get(action_info["action"], COLORS["dimmed"])
        if not action_info["available"]:
            color = dim(color, 90)
        blit_text(self._screen, label, (x_position, y_position), color, self._fonts.tiny, center=center)

    def _render_yellow(self, board: BoardDict, panel: pygame.Rect) -> None:
        grid = {(box["row"], box["col"]): box for box in board["yellow"]}
        box_size = min((panel.w - self._px(60)) // 4, (panel.h - self._px(56)) // 5)
        grid_width = 4 * (box_size + self._px(GRID_GAP))
        origin_x = panel.x + (panel.w - grid_width - self._px(24)) // 2
        block_height = 5 * (box_size + self._px(GRID_GAP)) + self._px(18)
        top_min = panel.y + self._px(CONTENT_Y)
        origin_y = top_min + max(0, (panel.bottom - top_min - block_height) // 2)

        for row in range(5):
            for column in range(4):
                self._render_yellow_cell(grid.get((row, column)), origin_x, origin_y, row, column, box_size)

        for row, action_info in board["yellow_row_actions"].items():
            if action_info:
                action_x = origin_x + grid_width + self._px(6)
                action_y = origin_y + row * (box_size + self._px(GRID_GAP)) + self._px(2)
                self._render_positional_action(action_info, action_x, action_y, center=False)

        for column, action_info in board["yellow_col_actions"].items():
            if action_info:
                action_x = origin_x + column * (box_size + self._px(GRID_GAP)) + box_size // 2
                action_y = origin_y + 5 * (box_size + self._px(GRID_GAP)) + self._px(2)
                self._render_positional_action(action_info, action_x, action_y, center=True)

    def _render_yellow_cell(
        self, box: YellowBoxDict | None, origin_x: int, origin_y: int,
        row: int, column: int, box_size: int,
    ) -> None:
        gap = self._px(GRID_GAP)
        radius = max(3, self._px(BOX_RADIUS))
        rect = pygame.Rect(origin_x + column * (box_size + gap), origin_y + row * (box_size + gap),
                           box_size, box_size)
        if box is None:
            pygame.draw.rect(self._screen, COLORS["sunken"], rect, border_radius=radius)
            return
        if box["crossed"]:
            fill = COLORS["crossed"]
        elif box["circled"]:
            fill = COLORS["circled"]
        else:
            fill = SECTION_COLORS["yellow"]
        pygame.draw.rect(self._screen, fill, rect, border_radius=radius)
        blit_text(self._screen, str(box["value"]), rect.center, CELL_TEXT_DARK, self._fonts.small, center=True)

    def _render_combined(self, board: BoardDict, panel: pygame.Rect) -> None:
        sections = [
            ("GREEN", SECTION_COLORS["green"], self._render_green, board["green"]),
            ("BLUE", SECTION_COLORS["blue"], self._render_blue, board["blue"]),
            ("PINK", SECTION_COLORS["pink"], self._render_pink, board["pink"]),
        ]
        section_height = panel.h // len(sections)
        for index, (name, accent, render_fn, data) in enumerate(sections):
            sub_rect = pygame.Rect(panel.x, panel.y + index * section_height, panel.w, section_height)
            accent_bar = pygame.Rect(sub_rect.x + self._px(PAD), sub_rect.y + self._px(HEADER_Y) + self._px(12),
                                     self._px(3), self._px(12))
            pygame.draw.rect(self._screen, accent, accent_bar, border_radius=2)
            blit_text(self._screen, name, (sub_rect.x + self._px(PAD) + self._px(8), sub_rect.y + self._px(HEADER_Y)),
                      COLORS["dimmed"], self._fonts.label)
            render_fn(data, sub_rect, accent)

    def _render_row_boxes(
        self, data: list, panel: pygame.Rect, accent: tuple,
        label_fn, filled_fn,
    ) -> None:
        count = len(data)
        gap = self._px(GRID_GAP)
        box_width = min((panel.w - 2 * self._px(PAD) - (count - 1) * gap) // count, self._px(ROW_BOX_MAX))
        origin_x = panel.x + (panel.w - (count * box_width + (count - 1) * gap)) // 2
        origin_y = panel.y + self._px(CONTENT_Y) + self._px(2)
        for index, box in enumerate(data):
            rect = pygame.Rect(origin_x + index * (box_width + gap), origin_y, box_width, box_width)
            self._draw_row_box(rect, accent, label_fn(box, index), filled_fn(box))
            self._render_action_label(box["action"], rect.centerx, origin_y + box_width + self._px(1))

    def _draw_row_box(self, rect: pygame.Rect, accent: tuple, label: str, filled: bool) -> None:
        radius = max(3, self._px(BOX_RADIUS))
        pygame.draw.rect(self._screen, accent if filled else COLORS["box_empty"], rect, border_radius=radius)
        text_color = CELL_TEXT_DARK if filled else COLORS["dimmed"]
        blit_text(self._screen, label, rect.center, text_color, self._fonts.tiny, center=True)

    def _render_blue(self, data: list[BlueBoxDict], panel: pygame.Rect, accent: tuple) -> None:
        self._render_row_boxes(
            data, panel, accent,
            lambda box, _: str(box["value_used"]) if box["value_used"] is not None else f"≤{box['max_limit']}",
            lambda box: box["value_used"] is not None,
        )

    def _render_green(self, data: list[GreenBoxDict], panel: pygame.Rect, accent: tuple) -> None:
        def label(box: GreenBoxDict, index: int) -> str:
            if box["value_used"] is not None:
                return str(box["value_used"])
            sign = "+" if index % 2 == 0 else "-"
            return f"{sign}{box['multiplier']}"
        self._render_row_boxes(data, panel, accent, label, lambda box: box["value_used"] is not None)

    def _render_pink(self, data: list[PinkBoxDict], panel: pygame.Rect, accent: tuple) -> None:
        def label(box: PinkBoxDict, _: int) -> str:
            if box["value_used"] is not None:
                return str(box["value_used"])
            return f"≥{box['filter_limit']}" if box["filter_limit"] else "—"
        self._render_row_boxes(data, panel, accent, label, lambda box: box["value_used"] is not None)

    def _render_grey(self, board: BoardDict, panel: pygame.Rect) -> None:
        color_names = ["yellow", "blue", "green", "pink"]
        rows_by_color: dict[str, list[GreyBoxDict]] = {color: [] for color in color_names}
        for box in board["grey"]:
            rows_by_color[box["color"]].append(box)

        box_size = min((panel.w - self._px(24)) // 6, (panel.h - self._px(56)) // 4)
        origin_x = panel.x + self._px(PAD)
        block_height = 4 * (box_size + self._px(GRID_GAP)) + self._px(18)
        top_min = panel.y + self._px(CONTENT_Y)
        origin_y = top_min + max(0, (panel.bottom - top_min - block_height) // 2)

        for row_index, color_name in enumerate(color_names):
            for column_index, box in enumerate(sorted(rows_by_color[color_name], key=lambda item: item["number"])):
                self._render_grey_cell(box, color_name, origin_x, origin_y, row_index, column_index, box_size)

        self._render_grey_col_actions(board, origin_x, origin_y, box_size)

    def _render_grey_col_actions(self, board: BoardDict, origin_x: int, origin_y: int, box_size: int) -> None:
        gap = self._px(GRID_GAP)
        action_y = origin_y + 4 * (box_size + gap) + self._px(2)
        for number, action_info in board["grey_col_actions"].items():
            if action_info:
                action_x = origin_x + (number - 1) * (box_size + gap) + box_size // 2
                self._render_positional_action(action_info, action_x, action_y, center=True)

    def _render_grey_cell(
        self, box: GreyBoxDict, color_name: str, origin_x: int, origin_y: int,
        row_index: int, column_index: int, box_size: int,
    ) -> None:
        gap = self._px(GRID_GAP)
        radius = max(3, self._px(BOX_RADIUS))
        rect = pygame.Rect(origin_x + column_index * (box_size + gap),
                           origin_y + row_index * (box_size + gap), box_size, box_size)
        fill = COLORS["crossed"] if box["crossed"] else dim(SECTION_COLORS.get(color_name, COLORS["box_empty"]), 50)
        pygame.draw.rect(self._screen, fill, rect, border_radius=radius)
        blit_text(self._screen, str(box["number"]), rect.center, COLORS["text"], self._fonts.tiny, center=True)
