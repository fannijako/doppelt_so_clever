from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field

from arcade import shape_list

from src.dice.dice import Dice
from src.board.board_types import (
    BoardDict, BlueBoxDict, GreenBoxDict, PinkBoxDict, YellowBoxDict, GreyBoxDict,
)
from src.ui.geometry import Rect
from src.ui.widgets import Painter
from src.ui.layout import Layout
from src.ui.theme import COLORS, SECTION_COLORS, ACTION_COLORS, with_alpha, mix, dim, type_size
from src.ui.constants import ACTION_LABELS, POPUP_ACTION_NAMES, POPUP_SOURCE_NAMES
from src.ui.render_snapshot import RenderSnapshot
from src.game.score_rating import get_score_rating

PAD = 14
HEADER_H = 40
GRID_GAP = 5
INK = (24, 26, 34)

LEGEND = [("R", "reroll", "reroll"), ("U", "reuse", "reuse"), ("+1", "plus one", "plus_one"),
          ("?", "question", "black_question_mark"), ("F", "fox", "fox")]


def option_label(option) -> str:
    if isinstance(option, str):
        return option.title()
    if isinstance(option, Dice):
        color = option.color.value.title() if option.color else ""
        if option.value is None:
            return color or "?"
        return f"{color}  {option.value}".strip()
    if isinstance(option, tuple):
        return _placement_label(option)
    action_type = getattr(option, "action_type", None)
    if action_type is not None:
        return POPUP_ACTION_NAMES.get(action_type.value, str(action_type.value))
    return str(option).title()


def _placement_label(option: tuple) -> str:
    if len(option) >= 3 and isinstance(option[-1], Enum) and isinstance(option[-1].value, str):
        cell = f"R{option[-3] + 1}·C{option[-2] + 1}"
        prefix = f"{option[0]}→" if len(option) == 4 else ""
        mark = " ○" if option[-1].value == "circle" else ""
        return f"{prefix}{cell}{mark}"
    return "  ".join(
        value.title() if isinstance(value := getattr(item, "value", item), str) else str(value)
        for item in option
    )


def fit_size(painter: Painter, label: str, button_w: int) -> int:
    available = button_w - painter.px(16)
    width = painter.text_width(label, painter.px(17), bold=True)
    if width <= available:
        return 17
    return max(9, int(17 * available / max(width, 1)))


@dataclass
class RenderTargets:
    buttons: list[Rect] = field(default_factory=list)
    dice: list[tuple] = field(default_factory=list)


@dataclass(frozen=True)
class _GridGeo:  # pylint: disable=too-many-instance-attributes
    cols: int
    button_w: int
    gap: int
    row_gap: int
    height: int
    start_x: int
    grid_top: int
    bottom: int
    prompt_y: int


class Renderer:
    def __init__(self, font: str | tuple[str, ...]) -> None:
        self._font = font
        self._bg: shape_list.ShapeElementList | None = None
        self._bg_size: tuple[int, int] | None = None
        self.mouse: tuple[int, int] = (-1, -1)

    def render(self, snapshot: RenderSnapshot, layout: Layout) -> RenderTargets:
        self._draw_background(layout)
        painter = Painter(layout.height, layout.scale, self._font)
        self._top_bar(painter, snapshot, layout)
        self._board(painter, snapshot.board_data, layout)
        targets = RenderTargets(dice=self._tray(painter, snapshot, layout))

        if snapshot.is_game_over and snapshot.score is not None:
            self._game_over(painter, snapshot, layout)
        elif snapshot.is_waiting and snapshot.options:
            targets.buttons = self._action_bar(painter, snapshot, layout)

        self._toasts(painter, snapshot.popup_notifications, layout)
        if snapshot.show_help:
            self._help(painter, layout)
        return targets

    def _draw_background(self, layout: Layout) -> None:
        size = (layout.width, layout.height)
        if self._bg is None or self._bg_size != size:
            width, height = size
            points = [(0, 0), (width, 0), (width, height), (0, height)]
            bottom, top = COLORS["background_bottom"], COLORS["background_top"]
            self._bg = shape_list.ShapeElementList()
            self._bg.append(shape_list.create_rectangle_filled_with_colors(points, [bottom, bottom, top, top]))
            self._bg_size = size
        self._bg.draw()

    # ---------- top bar ----------
    def _top_bar(self, painter: Painter, snapshot: RenderSnapshot, layout: Layout) -> None:
        top_bar = layout.top_bar
        painter.text("Doppelt so clever", top_bar.x, top_bar.y, COLORS["text"],
                     type_size("heading", layout.scale), bold=True)
        painter.text(self._round_caption(snapshot), top_bar.x, top_bar.y + painter.px(38),
                     COLORS["dimmed"], type_size("small", layout.scale))
        self._resource_rail(painter, snapshot, layout)

    @staticmethod
    def _round_caption(snapshot: RenderSnapshot) -> str:
        kind = "Active" if snapshot.is_active_round else "Passive"
        caption = f"Round {snapshot.round_number}   ·   {kind}"
        if snapshot.is_active_round and snapshot.subround > 0:
            caption += f"   ·   Turn {snapshot.subround}"
        return caption

    def _resource_rail(self, painter: Painter, snapshot: RenderSnapshot, layout: Layout) -> None:
        board = snapshot.board_data
        score = snapshot.display_score if snapshot.display_score is not None else snapshot.score
        segments = [
            ("SCORE", str(score) if score is not None else "–", COLORS["score"], 18),
            ("FOXES", str(board["foxes"]), ACTION_COLORS["fox"], 15),
            ("REROLL", self._ratio(board["rerolls"]), ACTION_COLORS["reroll"], 15),
            ("REUSE", self._ratio(board["reuses"]), ACTION_COLORS["reuse"], 15),
            ("PLUS-ONE", self._ratio(board["plus_ones"]), ACTION_COLORS["plus_one"], 15),
        ]
        height = painter.px(54)
        gap = painter.px(9)
        top = layout.top_bar.y + painter.px(2)
        cursor = layout.top_bar.right
        for label, value, color, value_size in reversed(segments):
            width = painter.px(max(len(label), len(value)) * 8 + 30)
            cursor -= width
            painter.pill(Rect(cursor, top, width, height), label, value, color, value_size)
            cursor -= gap

    @staticmethod
    def _ratio(counter: dict) -> str:
        return f"{counter['usable']}/{counter['gained']}"

    # ---------- board ----------
    def _board(self, painter: Painter, board: BoardDict, layout: Layout) -> None:
        yellow, mid, grey = layout.board_columns
        painter.card(yellow, accent=SECTION_COLORS["yellow"])
        self._card_header(painter, "YELLOW", yellow, SECTION_COLORS["yellow"], layout.scale)
        self._yellow(painter, board, yellow, layout.scale)

        painter.card(mid)
        self._mid_sections(painter, board, mid, layout.scale)

        painter.card(grey, accent=SECTION_COLORS["grey"])
        self._card_header(painter, "GREY", grey, SECTION_COLORS["grey"], layout.scale)
        self._grey(painter, board, grey, layout.scale)

    def _card_header(self, painter: Painter, name: str, panel: Rect, accent: tuple, scale: float) -> None:
        chip = Rect(panel.x + painter.px(PAD), panel.y + painter.px(16), painter.px(11), painter.px(11))
        painter.round_rect(chip, accent, painter.px(3))
        painter.text(name, chip.right + painter.px(8), panel.y + painter.px(14),
                     COLORS["dimmed"], type_size("label", scale), bold=True)

    def _content_top(self, painter: Painter, panel: Rect) -> int:
        return panel.y + painter.px(HEADER_H)

    def _yellow(self, painter: Painter, board: BoardDict, panel: Rect, scale: float) -> None:
        grid = {(box["row"], box["col"]): box for box in board["yellow"]}
        gap = painter.px(GRID_GAP)
        box_size = min((panel.w - painter.px(64)) // 4, (panel.h - painter.px(70)) // 5)
        grid_w = 4 * (box_size + gap)
        origin_x = panel.x + (panel.w - grid_w - painter.px(20)) // 2
        block_h = 5 * (box_size + gap)
        top = self._content_top(painter, panel)
        origin_y = top + max(0, (panel.bottom - top - block_h) // 2)

        for row in range(5):
            for col in range(4):
                rect = Rect(origin_x + col * (box_size + gap), origin_y + row * (box_size + gap), box_size, box_size)
                self._yellow_cell(painter, grid.get((row, col)), rect)
        for row, info in board["yellow_row_actions"].items():
            if info:
                self._action_glyph(painter, info, origin_x + grid_w + painter.px(2),
                                   origin_y + row * (box_size + gap) + box_size // 3, scale, centered=False)
        for col, info in board["yellow_col_actions"].items():
            if info:
                self._action_glyph(painter, info, origin_x + col * (box_size + gap) + box_size // 2,
                                   origin_y + block_h + painter.px(2), scale)

    def _yellow_cell(self, painter: Painter, box: YellowBoxDict | None, rect: Rect) -> None:
        if box is None:
            painter.round_rect(rect, COLORS["sunken"], painter.px(6))
            return
        marked = box["crossed"] or box["circled"]
        fill = SECTION_COLORS["yellow"] if marked else mix(SECTION_COLORS["yellow"], COLORS["panel"], 0.55)
        painter.box(rect, fill, label=str(box["value"]),
                    label_color=INK if marked else mix(SECTION_COLORS["yellow"], COLORS["text"], 0.5),
                    crossed=box["crossed"], circled=box["circled"])

    def _mid_sections(self, painter: Painter, board: BoardDict, panel: Rect, scale: float) -> None:
        rows = [
            ("GREEN", "green", board["green"], self._green_label),
            ("BLUE", "blue", board["blue"], self._blue_label),
            ("PINK", "pink", board["pink"], self._pink_label),
        ]
        row_h = panel.h // 3
        for index, (name, key, data, label_fn) in enumerate(rows):
            sub = Rect(panel.x, panel.y + index * row_h, panel.w, row_h)
            chip = Rect(sub.x + painter.px(PAD), sub.y + painter.px(14), painter.px(10), painter.px(10))
            painter.round_rect(chip, SECTION_COLORS[key], painter.px(2))
            painter.text(name, chip.right + painter.px(8), sub.y + painter.px(11),
                         COLORS["dimmed"], type_size("label", scale), bold=True)
            self._mid_row(painter, data, SECTION_COLORS[key], sub, label_fn, scale)

    def _mid_row(self, painter: Painter, data: list, accent: tuple, sub: Rect, label_fn, scale: float) -> None:
        count = len(data)
        gap = painter.px(GRID_GAP)
        box_w = min((sub.w - 2 * painter.px(PAD) - (count - 1) * gap) // count, painter.px(52))
        box_h = box_w - painter.px(4)
        grid_w = count * box_w + (count - 1) * gap
        origin_x = sub.x + (sub.w - grid_w) // 2
        origin_y = sub.y + painter.px(34)
        for index, box in enumerate(data):
            rect = Rect(origin_x + index * (box_w + gap), origin_y, box_w, box_h)
            filled = box["value_used"] is not None
            painter.box(rect, accent if filled else COLORS["box_empty"],
                        border=None if filled else COLORS["panel_border"],
                        label=label_fn(box, index), label_color=INK if filled else COLORS["muted"])
            self._action_glyph(painter, box["action"], rect.centerx, rect.bottom + painter.px(1), scale)

    @staticmethod
    def _green_label(box: GreenBoxDict, index: int) -> str:
        if box["value_used"] is not None:
            return str(box["value_used"])
        return f"{'+' if index % 2 == 0 else '-'}{box['multiplier']}"

    @staticmethod
    def _blue_label(box: BlueBoxDict, _: int) -> str:
        return str(box["value_used"]) if box["value_used"] is not None else f"≤{box['max_limit']}"

    @staticmethod
    def _pink_label(box: PinkBoxDict, _: int) -> str:
        if box["value_used"] is not None:
            return str(box["value_used"])
        return f"≥{box['filter_limit']}" if box["filter_limit"] else "—"

    GREY_ORDER = ["yellow", "blue", "green", "pink"]

    def _grey(self, painter: Painter, board: BoardDict, panel: Rect, scale: float) -> None:
        gap = painter.px(GRID_GAP)
        left_pad = painter.px(PAD + 8)
        avail_w = panel.w - left_pad - painter.px(PAD)
        box_size = min((avail_w - 5 * gap) // 6, (panel.h - painter.px(74)) // 4)
        block_h = 4 * (box_size + gap)
        grid_w = 6 * box_size + 5 * gap
        origin_x = panel.x + left_pad + (avail_w - grid_w) // 2
        top = self._content_top(painter, panel)
        origin_y = top + max(0, (panel.bottom - top - block_h) // 2)
        self._grey_cells(painter, board["grey"], (origin_x, origin_y), (box_size, gap))
        for number, info in board["grey_col_actions"].items():
            if info:
                self._action_glyph(painter, info, origin_x + (number - 1) * (box_size + gap) + box_size // 2,
                                   origin_y + block_h + painter.px(2), scale)

    def _grey_cells(self, painter: Painter, boxes: list, origin: tuple, cell: tuple) -> None:
        origin_x, origin_y = origin
        box_size, gap = cell
        by_color: dict[str, list[GreyBoxDict]] = {color: [] for color in self.GREY_ORDER}
        for box in boxes:
            by_color[box["color"]].append(box)
        for row, color in enumerate(self.GREY_ORDER):
            for col, box in enumerate(sorted(by_color[color], key=lambda item: item["number"])):
                rect = Rect(origin_x + col * (box_size + gap), origin_y + row * (box_size + gap), box_size, box_size)
                painter.box(rect, mix(SECTION_COLORS[color], COLORS["panel"], 0.35),
                            label=str(box["number"]), label_color=INK, crossed=box["crossed"])

    def _action_glyph(self, painter: Painter, action, x: int, y: int, scale: float, *, centered: bool = True) -> None:
        available = True
        if isinstance(action, dict):
            available = action["available"]
            action = action["action"]
        label = ACTION_LABELS.get(action, "")
        if not label:
            return
        color = ACTION_COLORS.get(action, COLORS["dimmed"])
        if not available:
            color = dim(color, 90)
        painter.text(label, x, y, color, type_size("tiny", scale), anchor_x="center" if centered else "left")

    # ---------- dice tray ----------
    def _tray(self, painter: Painter, snapshot: RenderSnapshot, layout: Layout) -> list[tuple]:
        panel = layout.tray
        painter.card(panel)
        painter.text("DICE", panel.x + painter.px(PAD), panel.y + painter.px(12),
                     COLORS["dimmed"], type_size("label", layout.scale), bold=True)
        die_size = min(panel.h - painter.px(66), painter.px(52))
        zones = [
            ("Available", snapshot.dice, snapshot.available_dice),
            ("Chosen", snapshot.picked_dice, snapshot.picked_dice),
            ("Discarded", snapshot.discarded_dice, []),
        ]
        targets: list[tuple] = []
        cursor = panel.x + painter.px(PAD + 6)
        for index, zone in enumerate(zones):
            zone_targets, cursor = self._tray_zone(painter, snapshot, panel, zone, cursor, die_size, layout.scale)
            targets.extend(zone_targets)
            if index < len(zones) - 1:
                painter.line(cursor - painter.px(18), panel.y + painter.px(28), cursor - painter.px(18),
                             panel.bottom - painter.px(16), COLORS["panel_border"], painter.px(1))
        return targets

    def _tray_zone(self, painter: Painter, snapshot: RenderSnapshot, panel: Rect, zone: tuple,
                   cursor: int, die_size: int, scale: float) -> tuple[list[tuple], int]:
        label, dice, bright = zone
        painter.text(label, cursor, panel.y + painter.px(30), COLORS["muted"], type_size("tiny", scale))
        row_y = panel.y + painter.px(56)
        targets: list[tuple] = []
        for die_index, die in enumerate(dice):
            rect = Rect(cursor + die_index * (die_size + painter.px(10)), row_y, die_size, die_size)
            self._draw_tray_die(painter, die, rect, bright, snapshot, scale)
            targets.append((die, rect))
        span = max(len(dice) * (die_size + painter.px(10)), painter.px(110))
        return targets, cursor + span + painter.px(28)

    def _draw_tray_die(self, painter: Painter, die, rect: Rect, bright: list,
                       snapshot: RenderSnapshot, scale: float) -> None:
        is_bright = any(die is other for other in bright)
        selectable = id(die) in snapshot.selectable_die_ids
        hinted = id(die) == snapshot.hint_die_id
        color_name = die.color.value if die.color else "white"
        painter.die(rect, color_name, die.value, available=is_bright or selectable,
                    selectable=selectable, pulse=snapshot.die_pulses.get(id(die), 0.0), hinted=hinted)
        if hinted:
            painter.text("HINT", rect.centerx, rect.y - painter.px(5), COLORS["hint"],
                         type_size("tiny", scale), anchor_x="center", anchor_y="bottom", bold=True)

    # ---------- action bar ----------
    def _action_bar(self, painter: Painter, snapshot: RenderSnapshot, layout: Layout) -> list[Rect]:
        action_bar = layout.action
        count = len(snapshot.options)
        gap = painter.px(10)
        prompt_w = painter.text_width(snapshot.prompt, type_size("body", layout.scale), bold=True)
        right_space = action_bar.right - (action_bar.x + prompt_w + painter.px(28))
        single_w = min(painter.px(168), (right_space - (count - 1) * gap) // max(count, 1))
        if single_w >= painter.px(84):
            painter.text(snapshot.prompt, action_bar.x, action_bar.y + painter.px(6), COLORS["prompt"],
                         type_size("body", layout.scale), bold=True)
            self._hint_hint(painter, snapshot, action_bar, layout.scale)
            return self._single_row(painter, snapshot, layout, single_w)
        return self._button_grid(painter, snapshot, layout)

    def _hint_hint(self, painter: Painter, snapshot: RenderSnapshot, action_bar: Rect, scale: float) -> None:
        line_y = action_bar.y + painter.px(34)
        painter.text("H  hint", action_bar.x, line_y, COLORS["muted"], type_size("label", scale))
        help_x = action_bar.x + painter.px(104)
        if snapshot.hint_uses > 0:
            painter.text(f"used {snapshot.hint_uses}×", help_x, line_y, COLORS["hint"], type_size("label", scale))
            help_x += painter.px(84)
        painter.text("?  help", help_x, line_y, COLORS["muted"], type_size("label", scale))

    def _single_row(self, painter: Painter, snapshot: RenderSnapshot, layout: Layout, button_w: int) -> list[Rect]:
        action_bar = layout.action
        options = snapshot.options
        count = len(options)
        gap = painter.px(10)
        height = painter.px(52)
        start_x = action_bar.right - (count * button_w + (count - 1) * gap)
        top = action_bar.y + (action_bar.h - height) // 2
        rects: list[Rect] = []
        for index, option in enumerate(options):
            rect = Rect(start_x + index * (button_w + gap), top, button_w, height)
            self._option_button(painter, snapshot, option, index, rect)
            rects.append(rect)
        return rects

    def _button_grid(self, painter: Painter, snapshot: RenderSnapshot, layout: Layout) -> list[Rect]:
        action_bar = layout.action
        geo = self._grid_geometry(painter, action_bar, len(snapshot.options))
        self._grid_header(painter, snapshot, action_bar, geo.prompt_y, geo.bottom, layout.scale)
        rects: list[Rect] = []
        for index, option in enumerate(snapshot.options):
            rect = Rect(geo.start_x + (index % geo.cols) * (geo.button_w + geo.gap),
                        geo.grid_top + (index // geo.cols) * (geo.height + geo.row_gap), geo.button_w, geo.height)
            self._option_button(painter, snapshot, option, index, rect)
            rects.append(rect)
        return rects

    @staticmethod
    def _grid_geometry(painter: Painter, action_bar: Rect, count: int) -> "_GridGeo":
        gap = painter.px(10)
        row_gap = painter.px(8)
        height = painter.px(44)
        inner = action_bar.w
        cols = min(count, max(1, (inner + gap) // (painter.px(90) + gap)))
        rows = -(-count // cols)
        button_w = min(painter.px(168), (inner - (cols - 1) * gap) // cols)
        start_x = action_bar.x + (inner - (cols * button_w + (cols - 1) * gap)) // 2
        bottom = action_bar.bottom - painter.px(8)
        grid_top = bottom - rows * height - (rows - 1) * row_gap
        return _GridGeo(cols, button_w, gap, row_gap, height, start_x, grid_top, bottom, grid_top - painter.px(30))

    def _grid_header(self, painter: Painter, snapshot: RenderSnapshot, action_bar: Rect,
                     prompt_y: int, bottom: int, scale: float) -> None:
        backdrop = Rect(action_bar.x - painter.px(6), prompt_y - painter.px(10),
                        action_bar.w + painter.px(12), bottom + painter.px(8) - (prompt_y - painter.px(10)))
        painter.round_rect(backdrop, with_alpha(COLORS["panel_raised"], 0.97), painter.px(12))
        painter.text(snapshot.prompt, action_bar.x + painter.px(4), prompt_y, COLORS["prompt"],
                     type_size("body", scale), bold=True)
        used = f"   (used {snapshot.hint_uses}×)" if snapshot.hint_uses > 0 else ""
        painter.text(f"H hint{used}     ?  help", action_bar.right - painter.px(4), prompt_y + painter.px(3),
                     COLORS["muted"], type_size("label", scale), anchor_x="right")

    def _option_button(self, painter: Painter, snapshot: RenderSnapshot, option, index: int,
                       rect: Rect) -> None:
        label = option_label(option)
        painter.button(rect, label, SECTION_COLORS.get(str(option), COLORS["prompt"]),
                       state=self._button_state(rect, index, snapshot.pressed_index),
                       is_hint=snapshot.hint_index == index,
                       size=fit_size(painter, label, rect.w))

    def _button_state(self, rect: Rect, index: int, pressed_index: int | None) -> str:
        if pressed_index == index:
            return "press"
        return "hover" if rect.collidepoint(*self.mouse) else "normal"

    # ---------- overlays ----------
    def _game_over(self, painter: Painter, snapshot: RenderSnapshot, layout: Layout) -> None:
        painter.veil(layout.width, (*COLORS["overlay"], 205))
        center_x = layout.width // 2
        middle = layout.height // 2
        painter.text("GAME OVER", center_x, middle - painter.px(60), COLORS["text"],
                     type_size("display", layout.scale), anchor_x="center", bold=True)
        painter.text(f"Score  {snapshot.score}", center_x, middle - painter.px(6),
                     COLORS["score"], type_size("display", layout.scale), anchor_x="center", bold=True)
        rating = get_score_rating(snapshot.score)
        if rating:
            painter.text(rating, center_x, middle + painter.px(48), COLORS["prompt"],
                         type_size("body", layout.scale), anchor_x="center")

    def _toasts(self, painter: Painter, popups: list[dict], layout: Layout) -> None:
        slots = layout.toast_slots(len(popups))
        for popup, rect in zip(popups[-len(slots):], slots):
            self._toast(painter, popup, rect)

    def _toast(self, painter: Painter, popup: dict, rect: Rect) -> None:
        alpha = popup["alpha"]
        color = ACTION_COLORS.get(popup["action"], COLORS["dimmed"])
        action = POPUP_ACTION_NAMES.get(popup["action"], popup["action"])
        source = POPUP_SOURCE_NAMES.get(popup["source"], popup["source"])
        painter.round_rect(rect, with_alpha(COLORS["panel_raised"], alpha), painter.px(9))
        painter.round_rect(Rect(rect.x, rect.y, painter.px(4), rect.h), with_alpha(color, alpha), painter.px(2))
        painter.text(f"Won {action}", rect.x + painter.px(14), rect.centery,
                     with_alpha(COLORS["text"], alpha), type_size("small"), anchor_y="center")
        painter.text(source, rect.right - painter.px(12), rect.centery,
                     with_alpha(COLORS["muted"], alpha), type_size("tiny"), anchor_x="right", anchor_y="center")

    def _help(self, painter: Painter, layout: Layout) -> None:
        painter.veil(layout.width, (*COLORS["overlay"], 224))
        lines = [
            ("Controls", COLORS["prompt"]),
            ("Click a highlighted die  —  pick it", COLORS["text"]),
            ("0 – 9  —  choose the numbered option", COLORS["text"]),
            ("H  —  ask the model for a hint", COLORS["text"]),
            ("F11  toggle fullscreen        Esc  quit", COLORS["dimmed"]),
        ]
        start_y = layout.height // 2 - painter.px(120)
        for index, (line, color) in enumerate(lines):
            size = type_size("heading" if index == 0 else "body", layout.scale)
            painter.text(line, layout.width // 2, start_y + index * painter.px(44), color, size,
                         anchor_x="center", bold=index == 0)
        self._help_legend(painter, layout, start_y + len(lines) * painter.px(44) + painter.px(24))

    def _help_legend(self, painter: Painter, layout: Layout, y: int) -> None:
        widths = [painter.px(len(glyph) * 9 + len(name) * 7 + 24) for glyph, name, _ in LEGEND]
        cursor = layout.width // 2 - sum(widths) // 2
        for (glyph, name, action), width in zip(LEGEND, widths):
            color = ACTION_COLORS.get(action, COLORS["dimmed"])
            painter.text(glyph, cursor, y, color, type_size("small", layout.scale), bold=True)
            painter.text(name, cursor + painter.px(len(glyph) * 9 + 6), y,
                         COLORS["muted"], type_size("tiny", layout.scale))
            cursor += width
