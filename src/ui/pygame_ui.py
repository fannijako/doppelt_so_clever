import logging
import sys
from typing import Optional, Callable, Any
from enum import Enum, auto

import pygame

from src.board.board import Board
from src.dice.dice import Dice
from src.actions.action_type import ActionType


class GameState(Enum):
    WAITING_FOR_INPUT = auto()
    ANIMATING = auto()
    IDLE = auto()


class Colors:  # pylint: disable=too-few-public-methods
    BG = (30, 30, 40)
    BG_LIGHT = (45, 45, 60)
    SECTION_BG = (50, 50, 65)
    TEXT = (240, 240, 240)
    TEXT_DIM = (150, 150, 150)
    BLUE = (65, 105, 225)
    BLUE_LIGHT = (100, 140, 255)
    PINK = (255, 105, 180)
    PINK_LIGHT = (255, 150, 200)
    GREEN = (50, 205, 50)
    GREEN_LIGHT = (100, 235, 100)
    YELLOW = (255, 215, 0)
    YELLOW_BG = (180, 160, 60)
    GREY = (128, 128, 128)
    WHITE = (255, 255, 255)
    BLACK = (20, 20, 20)
    RED = (220, 60, 60)
    ORANGE = (255, 165, 0)
    HIGHLIGHT = (255, 200, 100)
    BUTTON_BG = (60, 60, 80)
    BUTTON_HOVER = (80, 80, 110)
    BUTTON_ACTIVE = (100, 100, 140)

    ACTION_COLORS = {
        ActionType.REROLL: (100, 100, 255),
        ActionType.REUSE: (255, 105, 180),
        ActionType.PLUS_ONE: (255, 215, 0),
        ActionType.FOX: (255, 140, 0),
        ActionType.GREEN_QUESTION_MARK: (50, 205, 50),
        ActionType.YELLOW_QUESTION_MARK: (255, 215, 0),
        ActionType.BLUE_QUESTION_MARK: (65, 105, 225),
        ActionType.GREY_QUESTION_MARK: (128, 128, 128),
        ActionType.PINK_QUESTION_MARK: (255, 105, 180),
        ActionType.BLACK_QUESTION_MARK: (20, 20, 20),
    }

    @staticmethod
    def action_icon(action_type):
        icons = {
            ActionType.NONE: "",
            ActionType.REROLL: "\u21bb",
            ActionType.REUSE: "\u267b",
            ActionType.PLUS_ONE: "+1",
            ActionType.FOX: "\U0001F98A",
            ActionType.GREEN_QUESTION_MARK: "?",
            ActionType.YELLOW_QUESTION_MARK: "?",
            ActionType.BLUE_QUESTION_MARK: "?",
            ActionType.GREY_QUESTION_MARK: "?",
            ActionType.PINK_QUESTION_MARK: "?",
            ActionType.BLACK_QUESTION_MARK: "?",
        }
        return icons.get(action_type, "")


class Button:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        callback: Optional[Callable[[], Any]] = None,
        color_key: Optional[str] = None,
        enabled: bool = True
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color_key = color_key
        self.enabled = enabled
        self.hovered = False
        self.visible = True

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return

        if not self.enabled:
            bg_color = (50, 50, 60)
        elif self.hovered:
            bg_color = Colors.BUTTON_HOVER if self.enabled else (50, 50, 60)
        else:
            bg_color = Colors.BUTTON_BG if self.enabled else (50, 50, 60)

        pygame.draw.rect(screen, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(screen, Colors.TEXT_DIM, self.rect, 2, border_radius=6)

        text_surf = font.render(self.text, True, Colors.TEXT if self.enabled else Colors.TEXT_DIM)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
                return True

        return False


class PygameUI:  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    def __init__(self, board: Board):
        pygame.init()
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        pygame.display.set_caption("Doppelt So Clever")

        self.clock = pygame.time.Clock()
        self.board = board
        self.running = True

        self.font_large = pygame.font.SysFont("arial", 24, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 18)
        self.font_small = pygame.font.SysFont("arial", 14)
        self.font_tiny = pygame.font.SysFont("arial", 11)
        self.font_title = pygame.font.SysFont("arial", 32, bold=True)
        self.font_icon = pygame.font.SysFont("segoeuisymbol", 12)

        self.buttons: list[Button] = []
        self.current_dice: Optional[list[Dice]] = None
        self.discarded_dice: Optional[list[Dice]] = None
        self.picked_dice: Optional[list[Dice]] = None
        self.message: str = ""
        self.input_result: Any = None
        self.waiting_for_input = False
        self.input_type: Optional[str] = None
        self.input_options: list[Any] = []

        self.round_number: int = 0
        self.sub_round_number: int = 0
        self.is_passive: bool = False
        self.round_actions_label: str = ""
        self.banner_text: str = ""
        self.banner_timer: int = 0
        self.action_log: list[str] = []

        self.animation_time = 0

    def clear_buttons(self) -> None:
        self.buttons = []

    def add_button(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        value: Any = None,
        enabled: bool = True
    ) -> Button:
        def callback():
            self.input_result = value if value is not None else text
            self.waiting_for_input = False

        btn = Button(x, y, width, height, text, callback, enabled=enabled)
        self.buttons.append(btn)
        return btn

    def wait_for_input(self, input_type: str, options: list[Any], message: str) -> Any:
        self.input_type = input_type
        self.input_options = options
        self.message = message
        self.waiting_for_input = True
        self.input_result = None

        self._create_input_buttons(input_type, options)

        while self.waiting_for_input and self.running:
            self._handle_events()
            self._render()
            self.clock.tick(60)

        return self.input_result

    def _create_yes_no_buttons(self, button_y: int) -> None:
        self.add_button(520, button_y, 120, 60, "Yes", True)
        self.add_button(660, button_y, 120, 60, "No", False)

    def _create_dice_color_buttons(self, options: list[Any], button_y: int) -> None:

        colors = ["blue", "pink", "green", "yellow", "grey", "white"]
        option_strs = [str(o).lower() for o in options]
        matching = [c for c in colors if c in option_strs]
        x = (self.width - len(matching) * 110) // 2
        for color in colors:
            if color in option_strs:
                self.add_button(x, button_y, 100, 60, color.capitalize(), color)
                self.buttons[-1].color_key = color
                x += 110

    def _create_dice_index_buttons(self, options: list[Any], button_y: int) -> None:
        x = (self.width - len(options) * 140) // 2
        for i, die in enumerate(options):
            self.add_button(x, button_y, 130, 70, str(die), i)
            self.buttons[-1].color_key = str(die.color.value).lower()
            x += 140

    def _create_action_index_buttons(self, options: list[Any], button_y: int) -> None:
        items_per_row = 4
        button_width = 240
        button_height = 55
        spacing = 20
        start_x = (self.width - (items_per_row * (button_width + spacing) - spacing)) // 2
        for i, opt in enumerate(options):
            row = i // items_per_row
            col = i % items_per_row
            x = start_x + col * (button_width + spacing)
            y = button_y + row * (button_height + 10)
            self.add_button(x, y, button_width, button_height, str(opt), i)

    def _create_color_choice_buttons(self, options: list[Any], button_y: int) -> None:
        all_colors = ["yellow", "blue", "pink", "green", "grey"]
        option_strs = [
            str(o).lower().replace('dicecolor.', '') if hasattr(o, 'value') else str(o).lower()
            for o in options
        ]
        available = [c for c in all_colors if c in option_strs]
        x = (self.width - len(available) * 140) // 2
        for color in all_colors:
            if color in available:
                self.add_button(x, button_y, 130, 60, color.capitalize(), color)
                x += 140

    def _create_input_buttons(self, input_type: str, options: list[Any]) -> None:
        self.clear_buttons()

        button_y = self.height - 80

        if input_type == "yes_no":
            self._create_yes_no_buttons(button_y)
        elif input_type == "dice_color":
            self._create_dice_color_buttons(options, button_y)
        elif input_type == "dice_index":
            self._create_dice_index_buttons(options, button_y)
        elif input_type == "action_index":
            self._create_action_index_buttons(options, button_y)
        elif input_type == "color_choice":
            self._create_color_choice_buttons(options, button_y)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.waiting_for_input = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
                self.waiting_for_input = False
                pygame.quit()
                sys.exit()

            for btn in self.buttons:
                btn.handle_event(event)

    def _draw_section_panel(self, x, y, w, h, border_color=None, bg=None):
        bg = bg or Colors.SECTION_BG
        pygame.draw.rect(self.screen, bg, (x, y, w, h), border_radius=8)
        if border_color:
            pygame.draw.rect(self.screen, border_color, (x, y, w, h), 2, border_radius=8)

    def _draw_action_badge(self, x, y, action_type, size=16):
        if action_type == ActionType.NONE:
            return
        icon = Colors.action_icon(action_type)
        color = Colors.ACTION_COLORS.get(action_type, Colors.TEXT_DIM)
        pygame.draw.circle(self.screen, (40, 40, 50), (x + size // 2, y + size // 2), size // 2 + 1)
        pygame.draw.circle(self.screen, color, (x + size // 2, y + size // 2), size // 2)
        txt = self.font_tiny.render(icon, True, Colors.WHITE if action_type != ActionType.PLUS_ONE else Colors.BLACK)
        self.screen.blit(txt, (x + size // 2 - txt.get_width() // 2, y + size // 2 - txt.get_height() // 2))

    def _render(self) -> None:
        self.screen.fill(Colors.BG)
        self._draw_round_info_bar()

        board_x = 30
        board_w = self.width - 360
        top_y = 60

        self._draw_section_panel(board_x - 10, top_y - 10, board_w + 20, 185, Colors.GREY)
        self._draw_blue_section(board_x, top_y)
        self._draw_pink_section(board_x, top_y + 55)
        self._draw_green_section(board_x, top_y + 110)

        mid_y = top_y + 195
        half_w = (board_w - 20) // 2
        self._draw_section_panel(board_x - 10, mid_y, half_w + 10, 230, Colors.GREY)
        self._draw_grey_section(board_x, mid_y + 10)
        self._draw_section_panel(board_x + half_w + 10, mid_y, half_w + 10, 230, Colors.YELLOW, (60, 55, 30))
        self._draw_yellow_section(board_x + half_w + 20, mid_y + 10)

        track_y = mid_y + 245
        self._draw_blue_scoring_track(board_x, track_y, board_w)
        self._draw_resource_tracks(board_x, track_y + 45, board_w)

        self._draw_scoring(self.width - 310, top_y)
        self._draw_action_log(self.width - 310, top_y + 220)

        dice_y = self.height - 240
        if self.current_dice:
            self._draw_current_dice(board_x, dice_y)
        if self.picked_dice:
            self._draw_picked_dice(board_x + 500, dice_y)
        if self.discarded_dice:
            self._draw_discarded_plate(board_x, dice_y + 85)

        if self.message:
            msg_surf = self.font_large.render(self.message, True, Colors.HIGHLIGHT)
            self.screen.blit(msg_surf, (self.width // 2 - msg_surf.get_width() // 2, self.height - 150))

        for btn in self.buttons:
            btn.draw(self.screen, self.font_medium)

        if self.banner_text:
            self._draw_banner()

        pygame.display.flip()

    def _draw_blue_section(self, x: int, y: int) -> None:
        title = self.font_medium.render("BLUE", True, Colors.BLUE)
        self.screen.blit(title, (x, y + 5))

        box_w = 36
        box_h = 32
        gap = 3
        start_x = x + 55

        for i, box in enumerate(self.board.blue_board_part.boxes):
            bx = start_x + i * (box_w + gap)
            by = y

            bg = Colors.BLUE if box.value_used is not None else Colors.BG_LIGHT
            pygame.draw.rect(self.screen, bg, (bx, by, box_w, box_h), border_radius=3)
            pygame.draw.rect(self.screen, Colors.BLUE_LIGHT, (bx, by, box_w, box_h), 1, border_radius=3)

            if box.value_used is not None:
                vt = self.font_medium.render(str(box.value_used), True, Colors.WHITE)
                self.screen.blit(vt, (bx + box_w // 2 - vt.get_width() // 2, by + box_h // 2 - vt.get_height() // 2))
            else:
                lt = self.font_tiny.render(f"\u2264{box.maximum_value_limit}", True, Colors.TEXT_DIM)
                self.screen.blit(lt, (bx + box_w // 2 - lt.get_width() // 2, by + box_h // 2 - lt.get_height() // 2))

            self._draw_action_badge(bx + box_w // 2 - 8, by + box_h + 2, box.action)

    def _draw_pink_section(self, x: int, y: int) -> None:
        title = self.font_medium.render("PINK", True, Colors.PINK)
        self.screen.blit(title, (x, y + 5))

        r = 16
        gap = 3
        start_x = x + 55

        for i, box in enumerate(self.board.pink_board_part.boxes):
            cx = start_x + i * (r * 2 + gap) + r
            cy = y + r

            filled = box.value_used is not None
            bg = Colors.PINK if filled else Colors.BG_LIGHT
            pygame.draw.circle(self.screen, bg, (cx, cy), r)
            pygame.draw.circle(self.screen, Colors.PINK_LIGHT, (cx, cy), r, 1)

            if filled:
                vt = self.font_medium.render(str(box.value_used), True, Colors.WHITE)
                self.screen.blit(vt, (cx - vt.get_width() // 2, cy - vt.get_height() // 2))
            elif box.action_filter_limit > 0:
                lt = self.font_tiny.render(f"\u2265{box.action_filter_limit}", True, Colors.TEXT_DIM)
                self.screen.blit(lt, (cx - lt.get_width() // 2, cy - lt.get_height() // 2))

            self._draw_action_badge(cx - 8, cy + r + 2, box.action)

    def _draw_green_section(self, x: int, y: int) -> None:
        title = self.font_medium.render("GREEN", True, Colors.GREEN)
        self.screen.blit(title, (x, y + 5))

        r = 16
        gap = 3
        start_x = x + 55

        for i, box in enumerate(self.board.green_board_part.boxes):
            cx = start_x + i * (r * 2 + gap) + r
            cy = y + r

            filled = box.value_used is not None
            bg = Colors.GREEN if filled else Colors.BG_LIGHT
            pygame.draw.circle(self.screen, bg, (cx, cy), r)
            pygame.draw.circle(self.screen, Colors.GREEN_LIGHT, (cx, cy), r, 1)

            sign = "+" if box.index % 2 == 0 else "-"
            st = self.font_tiny.render(sign, True, Colors.GREEN_LIGHT)
            self.screen.blit(st, (cx - r + 2, cy - r + 1))

            mult_label = f"x{box.value_multiplier}" if box.value_multiplier > 1 else ""
            if mult_label and not filled:
                mt = self.font_tiny.render(mult_label, True, Colors.TEXT_DIM)
                self.screen.blit(mt, (cx - mt.get_width() // 2, cy - mt.get_height() // 2))
            elif filled:
                vt = self.font_medium.render(str(box.value_used), True, Colors.WHITE)
                self.screen.blit(vt, (cx - vt.get_width() // 2, cy - vt.get_height() // 2))

            self._draw_action_badge(cx - 8, cy + r + 2, box.action)

    def _draw_yellow_section(self, x: int, y: int) -> None:  # pylint: disable=too-many-locals
        title = self.font_medium.render("YELLOW", True, Colors.YELLOW)
        self.screen.blit(title, (x, y))

        box_size = 36
        gap = 4
        grid_x = x + 25
        grid_y = y + 25
        boxes_by_pos = {
            (b.row_position, b.column_position): b
            for b in self.board.yellow_board_part.boxes
        }

        col_actions = self.board.yellow_board_part._available_columns_for_action  # pylint: disable=protected-access
        for col in range(4):
            ax = grid_x + col * (box_size + gap) + box_size // 2
            if col in col_actions:
                self._draw_action_badge(ax - 8, grid_y - 20, col_actions[col])

        row_actions = self.board.yellow_board_part._available_rows_for_action  # pylint: disable=protected-access
        for row in range(5):
            ay = grid_y + row * (box_size + gap) + box_size // 2
            if row in row_actions:
                self._draw_action_badge(grid_x + 4 * (box_size + gap) + 4, ay - 8, row_actions[row])

        for row in range(5):
            for col in range(4):
                bx = grid_x + col * (box_size + gap)
                by = grid_y + row * (box_size + gap)

                box = boxes_by_pos.get((row, col))
                if box:
                    if box.is_crossed:
                        bg_color = (180, 50, 50)
                        text_color = Colors.WHITE
                        display = "X"
                    elif box.is_circled:
                        bg_color = Colors.YELLOW
                        text_color = Colors.BLACK
                        display = "O"
                    else:
                        bg_color = (80, 75, 40)
                        text_color = Colors.YELLOW
                        display = str(box.value)

                    pygame.draw.rect(self.screen, bg_color, (bx, by, box_size, box_size), border_radius=4)
                    pygame.draw.rect(self.screen, Colors.YELLOW, (bx, by, box_size, box_size), 1, border_radius=4)

                    text = self.font_medium.render(display, True, text_color)
                    tx = bx + box_size // 2 - text.get_width() // 2
                    ty = by + box_size // 2 - text.get_height() // 2
                    self.screen.blit(text, (tx, ty))
                else:
                    pygame.draw.rect(self.screen, (50, 48, 30), (bx, by, box_size, box_size), border_radius=4)
                    pygame.draw.rect(self.screen, (80, 75, 40), (bx, by, box_size, box_size), 1, border_radius=4)

    def _draw_grey_section(self, x: int, y: int) -> None:  # pylint: disable=too-many-locals
        box_w = 38
        box_h = 30
        gap = 3
        row_labels = ["Y", "B", "G", "P"]
        row_colors = [Colors.YELLOW, Colors.BLUE, Colors.GREEN, Colors.PINK]
        grid_x = x + 25
        grid_y = y + 22

        col_headers = ["1", "2", "3", "4", "5", "6"]
        for col_idx, hdr in enumerate(col_headers):
            hx = grid_x + col_idx * (box_w + gap) + box_w // 2
            ht = self.font_small.render(hdr, True, Colors.TEXT_DIM)
            self.screen.blit(ht, (hx - ht.get_width() // 2, grid_y - 16))

        for row_idx in range(4):
            row_boxes = self.board.grey_board_part.boxes[row_idx * 6:(row_idx + 1) * 6]
            rc = row_colors[row_idx]

            lbl_y = grid_y + row_idx * (box_h + gap) + box_h // 2
            pygame.draw.circle(self.screen, rc, (x + 10, lbl_y), 8)
            lt = self.font_tiny.render(row_labels[row_idx], True, Colors.BLACK)
            self.screen.blit(lt, (x + 10 - lt.get_width() // 2, lbl_y - lt.get_height() // 2))

            for col_idx, box in enumerate(row_boxes):
                bx = grid_x + col_idx * (box_w + gap)
                by = grid_y + row_idx * (box_h + gap)

                if box.is_crossed:
                    bg_color = rc
                    text_color = Colors.WHITE
                    display = "X"
                else:
                    bg_color = Colors.BG_LIGHT
                    text_color = Colors.WHITE
                    display = str(box.number)

                pygame.draw.rect(self.screen, bg_color, (bx, by, box_w, box_h), border_radius=3)
                pygame.draw.rect(self.screen, rc, (bx, by, box_w, box_h), 1, border_radius=3)

                text = self.font_medium.render(display, True, text_color)
                self.screen.blit(text, (bx + box_w // 2 - text.get_width() // 2, by + box_h // 2 - text.get_height() // 2))

        col_actions = self.board.grey_board_part._available_columns_for_action  # pylint: disable=protected-access
        for col_val in range(1, 7):
            if col_val in col_actions:
                ax = grid_x + (col_val - 1) * (box_w + gap) + box_w // 2 - 8
                ay = grid_y + 4 * (box_h + gap) + 4
                self._draw_action_badge(ax, ay, col_actions[col_val])

    def _draw_blue_scoring_track(self, x: int, y: int, w: int) -> None:
        scores = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78]
        num_used = len([b for b in self.board.blue_board_part.boxes if b.value_used is not None])

        self._draw_section_panel(x - 10, y, w + 20, 35, Colors.BLUE)
        r = 13
        gap = 4
        total_w = len(scores) * (r * 2 + gap) - gap
        sx = x + (w - total_w) // 2

        for i, score in enumerate(scores):
            cx = sx + i * (r * 2 + gap) + r
            cy = y + 18
            filled = i < num_used
            bg = Colors.BLUE if filled else (35, 35, 50)
            pygame.draw.circle(self.screen, bg, (cx, cy), r)
            pygame.draw.circle(self.screen, Colors.BLUE_LIGHT, (cx, cy), r, 1)
            st = self.font_tiny.render(str(score), True, Colors.WHITE if filled else Colors.TEXT_DIM)
            self.screen.blit(st, (cx - st.get_width() // 2, cy - st.get_height() // 2))

    def _draw_resource_tracks(self, x: int, y: int, w: int) -> None:
        tracks = [
            ("Rerolls", Colors.BLUE, self.board.gained_rerolls, self.board.usable_rerolls, 6),
            ("Reuses", Colors.PINK, self.board.gained_reuses, self.board.usable_reuses, 6),
            ("+1s", Colors.YELLOW, self.board.gained_plus_ones, self.board.usable_plus_ones, 6),
            ("Foxes", Colors.ORANGE, self.board.foxes, self.board.foxes, 4),
        ]

        row_h = 28
        for ti, (name, color, gained, usable, max_count) in enumerate(tracks):
            ty = y + ti * row_h
            self._draw_section_panel(x - 10, ty, w + 20, row_h - 3, color)

            nt = self.font_small.render(name, True, Colors.WHITE)
            self.screen.blit(nt, (x, ty + row_h // 2 - nt.get_height() // 2 - 1))

            r = 9
            gap = 4
            sx = x + 75
            for i in range(max_count):
                cx = sx + i * (r * 2 + gap) + r
                cy = ty + row_h // 2 - 1
                if i < gained:
                    if i < gained - usable:
                        bg = (60, 60, 70)
                    else:
                        bg = color
                else:
                    bg = (35, 35, 50)
                pygame.draw.circle(self.screen, bg, (cx, cy), r)
                pygame.draw.circle(self.screen, color, (cx, cy), r, 1)

    def _draw_round_info_bar(self) -> None:
        bar_rect = pygame.Rect(0, 0, self.width, 50)
        pygame.draw.rect(self.screen, Colors.BG_LIGHT, bar_rect)

        if self.round_number > 0:
            round_type = "PASSIVE ROUND" if self.is_passive else "ACTIVE ROUND"
            round_text = f"{round_type} {self.round_number}"
            if self.sub_round_number > 0 and not self.is_passive:
                round_text += f"  |  Sub-round {self.sub_round_number}/3"
            rt_surf = self.font_large.render(round_text, True, Colors.HIGHLIGHT)
            self.screen.blit(rt_surf, (20, 12))

        if self.round_actions_label:
            action_surf = self.font_medium.render(self.round_actions_label, True, Colors.TEXT)
            self.screen.blit(action_surf, (self.width // 2 - action_surf.get_width() // 2, 15))

        title = self.font_large.render("Doppelt So Clever", True, Colors.WHITE)
        self.screen.blit(title, (self.width - title.get_width() - 20, 12))

    def _draw_scoring(self, x: int, y: int) -> None:
        title = self.font_medium.render("SCORING", True, Colors.WHITE)
        self.screen.blit(title, (x, y))

        parts = [
            ("Blue", Colors.BLUE, self.board.blue_board_part.evaluate()),
            ("Pink", Colors.PINK, self.board.pink_board_part.evaluate()),
            ("Green", Colors.GREEN, self.board.green_board_part.evaluate()),
            ("Yellow", Colors.YELLOW, self.board.yellow_board_part.evaluate()),
            ("Grey", Colors.GREY, self.board.grey_board_part.evaluate()),
        ]
        fox_min = min(p[2] for p in parts) if parts else 0
        fox_score = self.board.foxes * fox_min
        total = sum(p[2] for p in parts) + fox_score

        for i, (name, color, score) in enumerate(parts):
            text = self.font_medium.render(f"{name}: {score}", True, color)
            self.screen.blit(text, (x, y + 25 + i * 22))

        fox_text = self.font_medium.render(
            f"Foxes ({self.board.foxes}x{fox_min}): {fox_score}", True, Colors.WHITE
        )
        self.screen.blit(fox_text, (x, y + 25 + len(parts) * 22))

        total_text = self.font_large.render(f"TOTAL: {total}", True, Colors.HIGHLIGHT)
        self.screen.blit(total_text, (x, y + 25 + (len(parts) + 1) * 22))

    def _draw_die(self, die: Dice, x: int, y: int, size: int = 60, dimmed: bool = False) -> None:
        color = getattr(Colors, die.color.name, Colors.WHITE)
        if dimmed:
            color = tuple(c // 2 for c in color)
        pygame.draw.rect(self.screen, color, (x, y, size, size), border_radius=8)
        border = Colors.TEXT_DIM if dimmed else Colors.WHITE
        pygame.draw.rect(self.screen, border, (x, y, size, size), 2, border_radius=8)

        if die.value is not None:
            value_text = self.font_large.render(str(die.value), True, Colors.BLACK)
            self.screen.blit(
                value_text,
                (x + size // 2 - value_text.get_width() // 2,
                 y + size // 2 - value_text.get_height() // 2),
            )
        color_text = self.font_small.render(die.color.name[:3], True, Colors.BLACK)
        self.screen.blit(color_text, (x + 4, y + 4))

    def _draw_current_dice(self, start_x: int, start_y: int) -> None:
        if not self.current_dice:
            return

        title = self.font_medium.render("Available Dice:", True, Colors.WHITE)
        self.screen.blit(title, (start_x, start_y))

        for i, die in enumerate(self.current_dice):
            self._draw_die(die, start_x + i * 80, start_y + 25)

    def _draw_picked_dice(self, start_x: int, start_y: int) -> None:
        if not self.picked_dice:
            return

        title = self.font_medium.render("Chosen Dice:", True, Colors.HIGHLIGHT)
        self.screen.blit(title, (start_x, start_y))

        for i, die in enumerate(self.picked_dice):
            self._draw_die(die, start_x + i * 80, start_y + 25)

    def _draw_discarded_plate(self, start_x: int, start_y: int) -> None:
        if not self.discarded_dice:
            return

        plate_w = max(len(self.discarded_dice) * 75 + 20, 200)
        plate_h = 120
        plate_rect = pygame.Rect(start_x, start_y, plate_w, plate_h)
        pygame.draw.rect(self.screen, (40, 40, 55), plate_rect, border_radius=10)
        pygame.draw.rect(self.screen, Colors.GREY, plate_rect, 2, border_radius=10)

        title = self.font_medium.render("Silver Platter (Discarded):", True, Colors.GREY)
        self.screen.blit(title, (start_x + 10, start_y + 5))

        for i, die in enumerate(self.discarded_dice):
            self._draw_die(die, start_x + 10 + i * 75, start_y + 30, size=55, dimmed=True)

    def _draw_banner(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        banner_h = 100
        banner_y = self.height // 2 - banner_h // 2
        banner_rect = pygame.Rect(0, banner_y, self.width, banner_h)
        pygame.draw.rect(self.screen, Colors.BG_LIGHT, banner_rect)
        pygame.draw.line(self.screen, Colors.HIGHLIGHT, (0, banner_y), (self.width, banner_y), 3)
        pygame.draw.line(
            self.screen, Colors.HIGHLIGHT,
            (0, banner_y + banner_h), (self.width, banner_y + banner_h), 3,
        )

        text = self.font_title.render(self.banner_text, True, Colors.HIGHLIGHT)
        self.screen.blit(
            text,
            (self.width // 2 - text.get_width() // 2, banner_y + banner_h // 2 - text.get_height() // 2),
        )

    def _draw_action_log(self, x: int, y: int) -> None:
        if not self.action_log:
            return

        title = self.font_medium.render("Actions:", True, Colors.WHITE)
        self.screen.blit(title, (x, y))

        for i, entry in enumerate(self.action_log):
            alpha = 255 - (len(self.action_log) - 1 - i) * 25
            color = (min(255, alpha), min(255, alpha), min(200, alpha))
            text = self.font_small.render(entry, True, color)
            self.screen.blit(text, (x, y + 22 + i * 18))

    def update_dice(
        self,
        dice: list[Dice],
        discarded: Optional[list[Dice]] = None,
        picked: Optional[list[Dice]] = None,
    ) -> None:
        self.current_dice = dice
        self.discarded_dice = discarded
        self.picked_dice = picked

    def set_round_info(
        self,
        round_number: int,
        sub_round: int = 0,
        is_passive: bool = False,
        round_action_label: str = "",
    ) -> None:
        self.round_number = round_number
        self.sub_round_number = sub_round
        self.is_passive = is_passive
        self.round_actions_label = round_action_label

    def show_banner(self, text: str, duration_frames: int = 90) -> None:
        self.banner_text = text
        self.banner_timer = duration_frames
        for _ in range(duration_frames):
            self._handle_events()
            self._render()
            self.clock.tick(60)
        self.banner_text = ""
        self.banner_timer = 0

    def log_action(self, text: str) -> None:
        self.action_log.append(text)
        if len(self.action_log) > 8:
            self.action_log.pop(0)

    def show_message(self, message: str) -> None:
        self.message = message
        logging.info(message)

    def refresh(self) -> None:
        self._render()
        pygame.event.pump()

    def close(self) -> None:
        pygame.quit()
