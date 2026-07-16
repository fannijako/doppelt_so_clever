from __future__ import annotations

import time
import threading
from typing import Any, TYPE_CHECKING

import arcade

from src.dice.dice import Dice
from src.board.board import Board
from src.ui.pick import build_pick_map
from src.ui.layout import Layout
from src.ui.renderer import Renderer, RenderTargets
from src.ui.animations import Animations
from src.logging_config import GameLogger
from src.ui.theme import load_ui_font, font_name_or_fallback
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
MIN_WINDOW_SIZE = (960, 640)
WINDOW_TITLE = "Doppelt So Clever"


class GameWindow(arcade.Window):
    def __init__(self, controller: "ArcadeUI", *, visible: bool = True) -> None:
        super().__init__(*DEFAULT_WINDOW_SIZE, WINDOW_TITLE, resizable=True, visible=visible)
        self.set_minimum_size(*MIN_WINDOW_SIZE)
        self.set_update_rate(1 / FRAMES_PER_SECOND)
        self._controller = controller

    def on_draw(self) -> None:
        self._controller.draw(self)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self._controller.mouse_motion(self, x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._controller.mouse_press(self, x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._controller.mouse_release(self, x, y)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self._controller.key_press(self, symbol)

    def on_text(self, text: str) -> None:
        self._controller.text(text)

    def on_close(self) -> None:
        self._controller.request_close(self)


class ArcadeUI(GameObserver):  # pylint: disable=too-many-instance-attributes

    def __init__(self, board: Board, model_advisor: ModelAdvisor | None = None, *, visible: bool = True) -> None:
        self.board = board
        self._model_advisor = model_advisor
        self.current_dice: list[Dice] = []
        self.available_dice: list[Dice] = []
        self._picked_dice: list[Dice] = []
        self._discarded_dice: list[Dice] = []
        self._round_number = 0
        self._is_active_round = True
        self._subround = 0
        self._score: int | None = None
        self._game_over = False
        self._won_actions: list[dict] = []
        self._hint_index: int | None = None
        self._hint_uses = 0

        self._lock = threading.Lock()
        self._input_event = threading.Event()
        self._input_result: Any = None
        self._prompt = ""
        self._options: list[Any] = []
        self._waiting = False
        self._pick_map: dict[int, int] = {}

        self._animations = Animations()
        self._window = GameWindow(self, visible=visible)
        self._renderer = Renderer(font_name_or_fallback(load_ui_font()))
        self._targets = RenderTargets()
        self._pressed_index: int | None = None
        self._show_help = False
        self._mouse = (-1, -1)
        self._game_thread: threading.Thread | None = None

    # ---------- observer events ----------
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

    def _hinted_die_id(self) -> int | None:
        if self._hint_index is None:
            return None
        return next((die_id for die_id, index in self._pick_map.items() if index == self._hint_index), None)

    # ---------- input bridge ----------
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
        logger.info("ArcadeUI observer close")
        self._input_event.set()

    # ---------- run loop ----------
    def run_with_game(self, game: Game) -> None:
        self._game_thread = threading.Thread(target=game.play, daemon=True)
        self._game_thread.start()
        arcade.run()
        self._game_thread.join(timeout=1)

    def draw(self, window: GameWindow) -> None:
        window.clear()
        self._renderer.mouse = self._mouse
        self._targets = self._renderer.render(self._take_snapshot(), Layout.compute(*window.get_size()))

    def _take_snapshot(self) -> RenderSnapshot:
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
                hint_die_id=self._hinted_die_id(),
                hint_uses=self._hint_uses,
                display_score=self._animations.displayed_score(),
                die_pulses={key: value for key, value in pulses.items() if value > 0.0},
                pressed_index=self._pressed_index,
                selectable_die_ids=set(self._pick_map),
                show_help=self._show_help,
            )

    # ---------- interaction ----------
    def mouse_motion(self, window: GameWindow, x: int, y: int) -> None:
        self._mouse = (x, window.height - y)

    def mouse_press(self, window: GameWindow, x: int, y: int) -> None:
        position = (x, window.height - y)
        with self._lock:
            if not self._waiting:
                return
            pick_map = dict(self._pick_map)
        for die, rect in self._targets.dice:
            if rect.collidepoint(*position) and id(die) in pick_map:
                self.submit_input(pick_map[id(die)])
                return
        for index, rect in enumerate(self._targets.buttons):
            if rect.collidepoint(*position):
                self._pressed_index = index
                return

    def mouse_release(self, window: GameWindow, x: int, y: int) -> None:
        pressed = self._pressed_index
        self._pressed_index = None
        if pressed is None or pressed >= len(self._targets.buttons):
            return
        if self._targets.buttons[pressed].collidepoint(x, window.height - y) and self._waiting:
            self.submit_input(pressed)

    def key_press(self, window: GameWindow, symbol: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self.request_close(window)
        elif symbol == arcade.key.F11:
            window.set_fullscreen(not window.fullscreen)

    def text(self, text: str) -> None:
        char = text.lower()
        if char == "?":
            self._show_help = not self._show_help
            return
        with self._lock:
            waiting = self._waiting
            count = len(self._options)
        if not waiting:
            return
        if char == "h":
            self._request_hint()
        elif text.isdigit() and 0 <= int(text) < count:
            self.submit_input(int(text))

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
            if recommendation is not None:
                self._hint_uses += 1

    def request_close(self, window: GameWindow) -> None:
        self._input_event.set()
        window.close()
