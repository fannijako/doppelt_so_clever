"""Pygame-based UI for Doppelt So Clever."""

import logging
import sys
from typing import Optional, Callable, Any
from enum import Enum, auto

import pygame

from src.board.board import Board
from src.dice.dice import Dice


class GameState(Enum):
    """Game states for UI flow control."""
    WAITING_FOR_INPUT = auto()
    ANIMATING = auto()
    IDLE = auto()


class Colors:  # pylint: disable=too-few-public-methods
    """Color palette."""
    BG = (30, 30, 40)
    BG_LIGHT = (45, 45, 60)
    TEXT = (240, 240, 240)
    TEXT_DIM = (150, 150, 150)
    BLUE = (65, 105, 225)
    PINK = (255, 105, 180)
    GREEN = (50, 205, 50)
    YELLOW = (255, 215, 0)
    GREY = (128, 128, 128)
    WHITE = (255, 255, 255)
    BLACK = (20, 20, 20)
    RED = (220, 60, 60)
    HIGHLIGHT = (255, 200, 100)
    BUTTON_BG = (60, 60, 80)
    BUTTON_HOVER = (80, 80, 110)
    BUTTON_ACTIVE = (100, 100, 140)


class Button:
    """Interactive button."""

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


class PygameUI:
    """Pygame UI for Doppelt So Clever."""

    WIDTH = 1200
    HEIGHT = 900

    def __init__(self, board: Board):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Doppelt So Clever")

        self.clock = pygame.time.Clock()
        self.board = board
        self.running = True

        # Fonts
        self.font_large = pygame.font.SysFont("arial", 24, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 18)
        self.font_small = pygame.font.SysFont("arial", 14)
        self.font_title = pygame.font.SysFont("arial", 32, bold=True)

        # UI State
        self.buttons: list[Button] = []
        self.current_dice: Optional[list[Dice]] = None
        self.discarded_dice: Optional[list[Dice]] = None
        self.message: str = ""
        self.input_result: Any = None
        self.waiting_for_input = False
        self.input_type: Optional[str] = None
        self.input_options: list[Any] = []

        # Animation
        self.animation_time = 0

    def clear_buttons(self) -> None:
        """Clear all buttons."""
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
        """Add a button that stores its value when clicked."""
        def callback():
            self.input_result = value if value is not None else text
            self.waiting_for_input = False

        btn = Button(x, y, width, height, text, callback, enabled=enabled)
        self.buttons.append(btn)
        return btn

    def wait_for_input(self, input_type: str, options: list[Any], message: str) -> Any:
        """Block until user makes a selection."""
        self.input_type = input_type
        self.input_options = options
        self.message = message
        self.waiting_for_input = True
        self.input_result = None

        # Create buttons based on input type
        self._create_input_buttons(input_type, options)

        # Event loop waiting for input
        while self.waiting_for_input and self.running:
            self._handle_events()
            self._render()
            self.clock.tick(60)

        return self.input_result

    def _create_yes_no_buttons(self, button_y: int) -> None:
        """Create yes/no buttons."""
        self.add_button(520, button_y, 120, 60, "Yes", True)
        self.add_button(660, button_y, 120, 60, "No", False)

    def _create_dice_color_buttons(self, options: list[Any], button_y: int) -> None:
        """Create color selection buttons."""
        colors = ["blue", "pink", "green", "yellow", "grey", "white"]
        option_strs = [str(o).lower() for o in options]
        matching = [c for c in colors if c in option_strs]
        x = (self.WIDTH - len(matching) * 110) // 2
        for color in colors:
            if color in option_strs:
                self.add_button(x, button_y, 100, 60, color.capitalize(), color)
                self.buttons[-1].color_key = color
                x += 110

    def _create_dice_index_buttons(self, options: list[Any], button_y: int) -> None:
        """Create dice index buttons."""
        x = (self.WIDTH - len(options) * 140) // 2
        for i, die in enumerate(options):
            self.add_button(x, button_y, 130, 70, str(die), i)
            self.buttons[-1].color_key = str(die.color.value).lower()
            x += 140

    def _create_action_index_buttons(self, options: list[Any], button_y: int) -> None:
        """Create action/placement index buttons."""
        items_per_row = 4
        button_width = 240
        button_height = 55
        spacing = 20
        start_x = (self.WIDTH - (items_per_row * (button_width + spacing) - spacing)) // 2
        for i, opt in enumerate(options):
            row = i // items_per_row
            col = i % items_per_row
            x = start_x + col * (button_width + spacing)
            y = button_y + row * (button_height + 10)
            self.add_button(x, y, button_width, button_height, str(opt), i)

    def _create_color_choice_buttons(self, options: list[Any], button_y: int) -> None:
        """Create color substitution buttons."""
        all_colors = ["yellow", "blue", "pink", "green", "grey"]
        option_strs = [
            str(o).lower().replace('dicecolor.', '') if hasattr(o, 'value') else str(o).lower()
            for o in options
        ]
        available = [c for c in all_colors if c in option_strs]
        x = (self.WIDTH - len(available) * 140) // 2
        for color in all_colors:
            if color in available:
                self.add_button(x, button_y, 130, 60, color.capitalize(), color)
                x += 140

    def _create_input_buttons(self, input_type: str, options: list[Any]) -> None:
        """Create appropriate buttons for the input type."""
        self.clear_buttons()

        button_y = 750

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
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.waiting_for_input = False
                pygame.quit()
                sys.exit()

            for btn in self.buttons:
                btn.handle_event(event)

    def _render(self) -> None:
        """Render the game screen."""
        self.screen.fill(Colors.BG)

        # Title
        title = self.font_title.render("Doppelt So Clever", True, Colors.WHITE)
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 10))

        # Draw all board sections - two column layout
        # Left column: Blue, Pink, Green
        self._draw_blue_section(30, 50)
        self._draw_pink_section(30, 160)
        self._draw_green_section(30, 270)

        # Right column: Yellow (top), Grey (bottom)
        self._draw_yellow_section(700, 50)
        self._draw_grey_section(700, 350)

        # Bottom left: Resources
        self._draw_resources(30, 380)

        # Draw current message - positioned above buttons at bottom
        if self.message:
            msg_surf = self.font_large.render(self.message, True, Colors.HIGHLIGHT)
            self.screen.blit(msg_surf, (self.WIDTH // 2 - msg_surf.get_width() // 2, 700))

        # Draw current dice if available
        if self.current_dice:
            self._draw_current_dice()

        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.screen, self.font_medium)

        pygame.display.flip()

    def _draw_blue_section(self, x: int, y: int) -> None:
        """Draw the blue section (12 boxes in a row)."""
        title = self.font_medium.render("BLUE", True, Colors.BLUE)
        self.screen.blit(title, (x, y))

        box_width = 35
        box_height = 45
        start_x = x + 60

        for i, box in enumerate(self.board.blue_board_part.boxes):
            bx = start_x + i * (box_width + 4)
            by = y

            # Background
            color = Colors.BLUE if box.value_used is not None else Colors.BG_LIGHT
            pygame.draw.rect(self.screen, color, (bx, by, box_width, box_height), border_radius=3)
            pygame.draw.rect(self.screen, Colors.WHITE, (bx, by, box_width, box_height), 1, border_radius=3)

            # Value text
            limit_text = self.font_small.render(str(box.maximum_value_limit), True, Colors.TEXT_DIM)
            self.screen.blit(limit_text, (bx + 2, by + 2))

            if box.value_used is not None:
                value_text = self.font_medium.render(str(box.value_used), True, Colors.WHITE)
                self.screen.blit(value_text, (bx + box_width // 2 - value_text.get_width() // 2, by + 20))

    def _draw_pink_section(self, x: int, y: int) -> None:
        """Draw the pink section (12 boxes in a row)."""
        title = self.font_medium.render("PINK", True, Colors.PINK)
        self.screen.blit(title, (x, y))

        box_width = 35
        box_height = 45
        start_x = x + 60

        for i, box in enumerate(self.board.pink_board_part.boxes):
            bx = start_x + i * (box_width + 4)
            by = y

            color = Colors.PINK if box.value_used is not None else Colors.BG_LIGHT
            pygame.draw.rect(self.screen, color, (bx, by, box_width, box_height), border_radius=3)
            pygame.draw.rect(self.screen, Colors.WHITE, (bx, by, box_width, box_height), 1, border_radius=3)

            limit_text = self.font_small.render(str(box.action_filter_limit), True, Colors.TEXT_DIM)
            self.screen.blit(limit_text, (bx + 2, by + 2))

            if box.value_used is not None:
                value_text = self.font_medium.render(str(box.value_used), True, Colors.WHITE)
                self.screen.blit(value_text, (bx + box_width // 2 - value_text.get_width() // 2, by + 20))

    def _draw_green_section(self, x: int, y: int) -> None:
        """Draw the green section (12 boxes with alternating signs)."""
        title = self.font_medium.render("GREEN", True, Colors.GREEN)
        self.screen.blit(title, (x, y))

        box_width = 35
        box_height = 45
        start_x = x + 60

        for i, box in enumerate(self.board.green_board_part.boxes):
            bx = start_x + i * (box_width + 4)
            by = y

            color = Colors.GREEN if box.value_used is not None else Colors.BG_LIGHT
            pygame.draw.rect(self.screen, color, (bx, by, box_width, box_height), border_radius=3)
            pygame.draw.rect(self.screen, Colors.WHITE, (bx, by, box_width, box_height), 1, border_radius=3)

            sign = "+" if box.index % 2 == 0 else "-"
            sign_text = self.font_small.render(sign, True, Colors.TEXT_DIM)
            self.screen.blit(sign_text, (bx + 2, by + 2))

            if box.value_used is not None:
                value_text = self.font_medium.render(str(box.value_used), True, Colors.WHITE)
                self.screen.blit(value_text, (bx + box_width // 2 - value_text.get_width() // 2, by + 20))

    def _draw_yellow_section(self, x: int, y: int) -> None:
        """Draw the yellow section (5 rows x 4 columns grid)."""
        title = self.font_medium.render("YELLOW", True, Colors.YELLOW)
        self.screen.blit(title, (x, y))

        box_size = 45
        boxes_by_pos = {
            (b.row_position, b.column_position): b
            for b in self.board.yellow_board_part.boxes
        }

        for row in range(5):
            for col in range(4):
                bx = x + col * (box_size + 5)
                by = y + 30 + row * (box_size + 5)

                box = boxes_by_pos.get((row, col))
                if box:
                    if box.is_crossed:
                        bg_color = Colors.RED
                        text_color = Colors.WHITE
                        display = "X"
                    elif box.is_circled:
                        bg_color = Colors.YELLOW
                        text_color = Colors.BLACK
                        display = "o"
                    else:
                        bg_color = Colors.BG_LIGHT
                        text_color = Colors.YELLOW
                        display = str(box.value)

                    pygame.draw.rect(self.screen, bg_color, (bx, by, box_size, box_size), border_radius=3)
                    pygame.draw.rect(self.screen, Colors.WHITE, (bx, by, box_size, box_size), 1, border_radius=3)

                    text = self.font_medium.render(display, True, text_color)
                    text_x = bx + box_size // 2 - text.get_width() // 2
                    text_y = by + box_size // 2 - text.get_height() // 2
                    self.screen.blit(text, (text_x, text_y))

    def _draw_grey_section(self, x: int, y: int) -> None:
        """Draw the grey section (4 rows x 6 values)."""
        title = self.font_medium.render("GREY", True, Colors.GREY)
        self.screen.blit(title, (x, y))

        box_width = 45
        box_height = 35
        row_labels = ["Y", "B", "B", "P"]
        row_colors = [Colors.YELLOW, Colors.BLUE, Colors.BLUE, Colors.PINK]

        for row_idx in range(4):
            row_boxes = self.board.grey_board_part.boxes[row_idx * 6:(row_idx + 1) * 6]
            label = self.font_medium.render(row_labels[row_idx], True, row_colors[row_idx])
            self.screen.blit(label, (x, y + 35 + row_idx * (box_height + 5)))

            for col_idx, box in enumerate(row_boxes):
                bx = x + 30 + col_idx * (box_width + 5)
                by = y + 30 + row_idx * (box_height + 5)

                if box.is_crossed:
                    bg_color = Colors.GREY
                    text_color = Colors.WHITE
                    display = "X"
                else:
                    bg_color = Colors.BG_LIGHT
                    text_color = Colors.WHITE
                    display = str(box.number)

                pygame.draw.rect(self.screen, bg_color, (bx, by, box_width, box_height), border_radius=3)
                pygame.draw.rect(self.screen, Colors.WHITE, (bx, by, box_width, box_height), 1, border_radius=3)

                text = self.font_medium.render(display, True, text_color)
                text_x = bx + box_width // 2 - text.get_width() // 2
                text_y = by + box_height // 2 - text.get_height() // 2
                self.screen.blit(text, (text_x, text_y))

    def _draw_resources(self, x: int, y: int) -> None:
        """Draw resources section."""
        title = self.font_medium.render("RESOURCES", True, Colors.WHITE)
        self.screen.blit(title, (x, y))

        resources = [
            (f"Foxes: {self.board.foxes}", Colors.WHITE),
            (f"Rerolls: {self.board.usable_rerolls}", Colors.BLUE),
            (f"Plus Ones: {self.board.usable_plus_ones}", Colors.YELLOW),
            (f"Reuses: {self.board.usable_reuses}", Colors.PINK),
        ]

        for i, (text, color) in enumerate(resources):
            surf = self.font_medium.render(text, True, color)
            self.screen.blit(surf, (x, y + 25 + i * 25))

    def _draw_current_dice(self) -> None:
        """Draw current available dice."""
        if not self.current_dice:
            return

        y = 600
        title = self.font_medium.render("Available Dice:", True, Colors.WHITE)
        self.screen.blit(title, (50, y))

        for i, die in enumerate(self.current_dice):
            x = 50 + i * 80
            color = getattr(Colors, die.color.name, Colors.WHITE)
            pygame.draw.rect(self.screen, color, (x, y + 30, 60, 60), border_radius=8)
            pygame.draw.rect(self.screen, Colors.WHITE, (x, y + 30, 60, 60), 2, border_radius=8)

            if die.value is not None:
                value_text = self.font_large.render(str(die.value), True, Colors.BLACK)
                vt_x = x + 30 - value_text.get_width() // 2
                vt_y = y + 60 - value_text.get_height() // 2
                self.screen.blit(value_text, (vt_x, vt_y))

            color_text = self.font_small.render(die.color.name[:3], True, Colors.BLACK)
            self.screen.blit(color_text, (x + 5, y + 35))

    def update_dice(self, dice: list[Dice], discarded: Optional[list[Dice]] = None) -> None:
        """Update current dice display."""
        self.current_dice = dice
        self.discarded_dice = discarded

    def show_message(self, message: str) -> None:
        """Show a message to the user."""
        self.message = message
        logging.info(message)

    def refresh(self) -> None:
        """Refresh the display."""
        self._render()
        pygame.event.pump()

    def close(self) -> None:
        """Close the pygame window."""
        pygame.quit()
