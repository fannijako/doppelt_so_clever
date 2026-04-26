# pylint: disable=too-many-instance-attributes
from __future__ import annotations

import threading
from typing import Any, TYPE_CHECKING

import pygame

from src.board.board import Board
from src.ui.renderer import Renderer
from src.logging_config import GameLogger
from src.ui.constants import FRAMES_PER_SECOND
from src.game.game_observer import GameObserver
from src.ui.render_snapshot import RenderSnapshot
from src.actions.action_source import ActionSource

if TYPE_CHECKING:
    from src.dice.dice import Dice
    from src.game.game import Game
    from src.actions.base_action import Action

logger = GameLogger(__name__)


class PygameUI(GameObserver):

    def __init__(self, board: Board):
        self.board = board
        self.current_dice: list[Dice] = []
        self.available_dice: list[Dice] = []
        self._round_number: int = 0
        self._score: int | None = None
        self._game_over = False

        self._lock = threading.Lock()
        self._input_event = threading.Event()
        self._input_result: Any = None
        self._prompt: str = ""
        self._options: list[Any] = []
        self._waiting = False

        self._renderer: Renderer | None = None
        self._clock: pygame.time.Clock | None = None
        self._button_rects: list[pygame.Rect] = []

    def init_display(self) -> None:
        pygame.init()
        display_info = pygame.display.Info()
        screen = pygame.display.set_mode(
            (display_info.current_w, display_info.current_h),
            pygame.FULLSCREEN | pygame.SCALED,
        )
        pygame.display.set_caption("Doppelt So Clever")
        self._renderer = Renderer(
            screen=screen,
            font_regular=pygame.font.SysFont("monospace", 18),
            font_small=pygame.font.SysFont("monospace", 14),
            font_large=pygame.font.SysFont("monospace", 28, bold=True),
        )
        self._clock = pygame.time.Clock()

    def on_round_started(self, round_number: int) -> None:
        with self._lock:
            self._round_number = round_number

    def on_round_completed(self, round_number: int) -> None:
        pass

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        with self._lock:
            self.current_dice = list(dice)
            self.available_dice = list(dice)

    def on_die_picked(self, die: Dice, discarded: list[Dice], available: list[Dice]) -> None:
        with self._lock:
            self.available_dice = list(available)

    def on_board_updated(self) -> None:
        pass

    def on_game_ended(self, score: int) -> None:
        with self._lock:
            self._score = score
            self._game_over = True

    def on_action_executed(self, source: ActionSource, actions: list[Action]) -> None:
        pass

    def wait_for_input(self, prompt: str, options: list[Any]) -> int:
        logger.info("UI waiting for input", prompt, f"options={options}")
        with self._lock:
            self._prompt = prompt
            self._options = list(options)
            self._waiting = True
            self._button_rects = []
        self._input_result = None
        self._input_event.clear()
        self._input_event.wait()
        with self._lock:
            self._waiting = False
        return self._input_result  # type: ignore[return-value]

    def submit_input(self, result: Any) -> None:
        self._input_result = result
        self._input_event.set()

    def close(self) -> None:
        logger.info("PygameUI closed")
        self._input_event.set()

    def run_with_game(self, game: Game) -> None:
        game_thread = threading.Thread(target=game.play, daemon=True)
        game_thread.start()
        self.run_loop()
        game_thread.join(timeout=1)

    def run_loop(self) -> None:
        self.init_display()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._input_event.set()
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_key_press(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_mouse_click(event.pos)

            self._render()
            self._clock.tick(FRAMES_PER_SECOND)  # type: ignore[union-attr]
        pygame.quit()

    def _handle_key_press(self, event: pygame.event.Event) -> bool:
        if event.key == pygame.K_ESCAPE:
            self._input_event.set()
            return False

        with self._lock:
            if not self._waiting:
                return True
            options = self._options

        if pygame.K_0 <= event.key <= pygame.K_9:
            index = event.key - pygame.K_0
            if 0 <= index < len(options):
                self.submit_input(index)
        return True

    def _handle_mouse_click(self, position: tuple[int, int]) -> None:
        with self._lock:
            if not self._waiting:
                return
            button_rects = list(self._button_rects)
        for index, rect in enumerate(button_rects):
            if rect.collidepoint(position):
                self.submit_input(index)
                return

    def _take_render_snapshot(self) -> RenderSnapshot:
        with self._lock:
            return RenderSnapshot(
                board_data=self.board.to_dict(),
                dice=list(self.current_dice),
                available_dice=list(self.available_dice),
                round_number=self._round_number,
                prompt=self._prompt,
                options=list(self._options),
                is_waiting=self._waiting,
                score=self._score,
                is_game_over=self._game_over,
            )

    def _render(self) -> None:
        if self._renderer is None:
            return
        snapshot = self._take_render_snapshot()
        button_rects = self._renderer.render(snapshot)
        with self._lock:
            self._button_rects = button_rects
