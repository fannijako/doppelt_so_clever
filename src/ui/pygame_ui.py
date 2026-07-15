# pylint: disable=too-many-instance-attributes
from __future__ import annotations

import time
import threading
from typing import Any, TYPE_CHECKING

import pygame

from src.dice.dice import Dice
from src.board.board import Board
from src.ui.theme import load_fonts
from src.ui.layout import Layout
from src.ui.renderer import Renderer, RenderTargets
from src.logging_config import GameLogger
from src.ui.pick import build_pick_map
from src.ui.animations import Animations
from src.ui.constants import FRAMES_PER_SECOND
from src.game.game_observer import GameObserver
from src.ui.render_snapshot import RenderSnapshot
from src.actions.action_source import ActionSource
from src.ui.user_quit_exception import UserQuitException

if TYPE_CHECKING:
    from src.game.game import Game
    from src.actions.base_action import Action
    from src.ui.model_advisor import ModelAdvisor

logger = GameLogger(__name__)

DEFAULT_WINDOW_SIZE = (1280, 800)


class PygameUI(GameObserver):

    def __init__(self, board: Board, model_advisor: ModelAdvisor | None = None):
        self.board = board
        self._model_advisor = model_advisor
        self.current_dice: list[Dice] = []
        self.available_dice: list[Dice] = []
        self._picked_dice: list[Dice] = []
        self._discarded_dice: list[Dice] = []
        self._round_number: int = 0
        self._is_active_round: bool = True
        self._subround: int = 0
        self._score: int | None = None
        self._game_over = False
        self._won_actions: list[dict] = []
        self._hint_index: int | None = None

        self._lock = threading.Lock()
        self._input_event = threading.Event()
        self._input_result: Any = None
        self._prompt: str = ""
        self._options: list[Any] = []
        self._waiting = False
        self._pick_map: dict[int, int] = {}

        self._animations = Animations()
        self._renderer: Renderer | None = None
        self._clock: pygame.time.Clock | None = None
        self._targets = RenderTargets()
        self._pressed_index: int | None = None
        self._show_help = False
        self._is_fullscreen = False
        self._windowed_size = DEFAULT_WINDOW_SIZE

    def init_display(self) -> None:
        pygame.init()
        info = pygame.display.Info()
        self._windowed_size = (
            min(DEFAULT_WINDOW_SIZE[0], info.current_w),
            min(DEFAULT_WINDOW_SIZE[1], info.current_h),
        )
        screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption("Doppelt So Clever")
        self._renderer = Renderer(screen, load_fonts())
        self._clock = pygame.time.Clock()

    def _apply_display(self, size: tuple[int, int], flags: int) -> None:
        screen = pygame.display.set_mode(size, flags)
        if self._renderer is not None:
            self._renderer.screen = screen

    def _toggle_fullscreen(self) -> None:
        self._is_fullscreen = not self._is_fullscreen
        if self._is_fullscreen:
            self._apply_display((0, 0), pygame.FULLSCREEN | pygame.SCALED)
        else:
            self._apply_display(self._windowed_size, pygame.RESIZABLE)

    def on_round_started(self, round_number: int) -> None:
        with self._lock:
            self._round_number = round_number
            self._set_score(self.board.partial_evaluate())

    def on_round_completed(self, round_number: int) -> None:
        pass

    def on_active_round_started(self) -> None:
        with self._lock:
            self._is_active_round = True
            self._subround = 0
            self._picked_dice = []
            self._discarded_dice = []

    def on_passive_round_started(self) -> None:
        with self._lock:
            self._is_active_round = False
            self._subround = 0
            self._picked_dice = []
            self._discarded_dice = []

    def on_subround_started(self, subround: int) -> None:
        with self._lock:
            self._subround = subround

    def on_dice_rolled(self, dice: list[Dice]) -> None:
        with self._lock:
            self.current_dice = list(dice)
            self.available_dice = list(dice)

    def on_die_picked(self, die: Dice, discarded: list[Dice], available: list[Dice]) -> None:
        with self._lock:
            self.available_dice = list(available)
            self._picked_dice.append(die)
            self._discarded_dice.extend(discarded)
            self._animations.pulse(id(die), time.monotonic())

    def on_board_updated(self) -> None:
        with self._lock:
            self._set_score(self.board.partial_evaluate())

    def on_game_ended(self, score: int) -> None:
        with self._lock:
            self._set_score(score)
            self._game_over = True

    def on_action_executed(self, source: ActionSource, actions: list[Action]) -> None:
        now = time.monotonic()
        with self._lock:
            for action in actions:
                self._won_actions.append({"action": action.action_type.value, "source": source.value})
                self._animations.add_popup(action.action_type.value, source.value, now)

    def _set_score(self, score: int | None) -> None:
        self._score = score
        if score is not None:
            self._animations.set_score(score)

    def wait_for_input(self, prompt: str, options: list[Any]) -> int:
        logger.info("UI waiting for input", prompt, f"options={options}")
        with self._lock:
            self._prompt = prompt
            self._options = list(options)
            self._waiting = True
            self._hint_index = None
            pool = self.current_dice + self._picked_dice + self._discarded_dice + self.available_dice
            self._pick_map = build_pick_map(self._options, pool)
        self._input_result = None
        self._input_event.clear()
        self._input_event.wait()
        with self._lock:
            self._waiting = False
            self._pick_map = {}
        if self._input_result is None:
            raise UserQuitException("User quit while waiting for input")
        return self._input_result

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
                running = self._handle_event(event)
                if not running:
                    break
            self._render()
            self._clock.tick(FRAMES_PER_SECOND)  # type: ignore[union-attr]
        pygame.quit()

    def _handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            self._input_event.set()
            return False
        if event.type == pygame.VIDEORESIZE and not self._is_fullscreen:
            self._windowed_size = (event.w, event.h)
            self._apply_display(self._windowed_size, pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            return self._handle_key_press(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_mouse_up(event.pos)
        return True

    def _handle_key_press(self, event: pygame.event.Event) -> bool:
        if event.key == pygame.K_ESCAPE:
            self._input_event.set()
            return False
        if event.key == pygame.K_F11:
            self._toggle_fullscreen()
            return True
        if event.unicode == "?":
            self._show_help = not self._show_help
            return True

        with self._lock:
            waiting = self._waiting
            options = self._options
        if not waiting:
            return True
        if event.key == pygame.K_h:
            self._request_hint()
        elif pygame.K_0 <= event.key <= pygame.K_9:
            index = event.key - pygame.K_0
            if 0 <= index < len(options):
                self.submit_input(index)
        return True

    def _request_hint(self) -> None:
        if self._model_advisor is None:
            return
        with self._lock:
            num_options = len(self._options)
            prompt = self._prompt
        if num_options < 1:
            return
        recommendation = self._model_advisor.get_recommendation(num_options, prompt)
        with self._lock:
            self._hint_index = recommendation

    def _handle_mouse_down(self, position: tuple[int, int]) -> None:
        with self._lock:
            if not self._waiting:
                return
            pick_map = dict(self._pick_map)
        for die, rect in self._targets.dice:
            if rect.collidepoint(position) and id(die) in pick_map:
                self.submit_input(pick_map[id(die)])
                return
        for index, rect in enumerate(self._targets.buttons):
            if rect.collidepoint(position):
                self._pressed_index = index
                return

    def _handle_mouse_up(self, position: tuple[int, int]) -> None:
        pressed = self._pressed_index
        self._pressed_index = None
        if pressed is None or pressed >= len(self._targets.buttons):
            return
        if self._targets.buttons[pressed].collidepoint(position) and self._waiting:
            self.submit_input(pressed)

    def _take_render_snapshot(self) -> RenderSnapshot:
        now = time.monotonic()
        with self._lock:
            self._animations.update(now)
            pulses = {id(die): self._animations.pulse_intensity(id(die), now)
                      for die in self.current_dice + self._picked_dice + self._discarded_dice}
            return RenderSnapshot(
                board_data=self.board.to_dict(),
                dice=list(self.current_dice),
                available_dice=list(self.available_dice),
                picked_dice=list(self._picked_dice),
                discarded_dice=list(self._discarded_dice),
                round_number=self._round_number,
                is_active_round=self._is_active_round,
                subround=self._subround,
                prompt=self._prompt,
                options=list(self._options),
                is_waiting=self._waiting,
                score=self._score,
                is_game_over=self._game_over,
                won_actions=list(self._won_actions),
                popup_notifications=self._animations.active_popups(now),
                hint_index=self._hint_index,
                display_score=self._animations.displayed_score(),
                die_pulses={key: value for key, value in pulses.items() if value > 0.0},
                pressed_index=self._pressed_index,
                selectable_die_ids=set(self._pick_map),
                show_help=self._show_help,
            )

    def _render(self) -> None:
        if self._renderer is None:
            return
        layout = Layout.compute(*self._renderer.screen.get_size())
        self._targets = self._renderer.render(self._take_render_snapshot(), layout)
