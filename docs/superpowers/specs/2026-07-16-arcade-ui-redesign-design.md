# Interactive UI Redesign — Arcade migration

**Date:** 2026-07-16
**Status:** Implemented
**Supersedes:** `2026-07-15-pygame-ui-upgrade-design.md` (pygame reskin — replaced, not extended)

## Goal

Redesign the interactive UI. Switch the rendering toolkit from **pygame → Arcade 3.x**
and rebuild the whole view layer to a coherent "Refined dark" design. Game logic,
observers, threading model, `InputHandler`, and the `RenderSnapshot` seam are unchanged.

## Decision

The plumbing (observer pattern, threaded game/render split, `RenderSnapshot`) was healthy
and framework-agnostic; only the presentation was weak. Arcade (OpenGL, built on pyglet)
buys crisp anti-aliased shapes, real font rendering, `arcade.gui`-grade widgets, and
easing — a higher ceiling than raw pygame at moderate migration cost. `main.py play
--mode interactive` and the native-window run model are preserved. pygame lived only in
`src/ui/*` + `test/ui/*`, so the swap is contained.

Alternatives considered: stay-in-pygame reskin (lower ceiling), web UI (server + browser —
changes the run model, much larger rework), pygame_gui / pyglet / DearPyGui (see the
toolkit trade-off in the session).

## Architecture

Same threaded design as before, re-expressed for Arcade:

- **`ArcadeUI(GameObserver)`** — controller + observer. Owns a `GameWindow(arcade.Window)`
  by **composition** (subclassing `arcade.Window` *and* the `GameObserver` ABC hits a
  metaclass conflict). `GameWindow` forwards `on_draw`/mouse/key/`on_close` to the
  controller.
- Game runs on a daemon thread; `wait_for_input(prompt, options) -> int` blocks on a
  `threading.Event`; the window renders every frame from a locked snapshot. Identical
  bridge contract to the old `PygameUI`.
- `close()` keeps the observer meaning (unblock at game-end, window stays open on
  GAME OVER); the window is closed only via `on_close`/Esc → `arcade.Window.close`.

## Module layout (`src/ui/`)

| File | Responsibility |
|------|----------------|
| `theme.py` | Refined-dark palette, Inter loader (`arcade.load_font`), 8px spacing + type ramp, `dim`/`mix`/`with_alpha` |
| `geometry.py` *(new)* | `Rect` value type (top-left coords) — toolkit-agnostic, unit-testable without GL |
| `layout.py` | Responsive regions from window size: top bar (title + score/resource rail), board row (yellow \| green-blue-pink \| grey), full-width dice tray, action bar; min-clamp + reflow; toast slots |
| `widgets.py` | `Painter`: coordinate flip, rounded-rect (built from primitives), Inter text (cached), card/die/box/pill/button |
| `renderer.py` | `Renderer.render(snapshot, layout) -> RenderTargets`; draws chrome + board + tray + toasts + overlays; returns die/button hit-boxes |
| `animations.py`, `pick.py`, `constants.py`, `render_snapshot.py` | unchanged (framework-agnostic) |
| `arcade_ui.py` *(was `pygame_ui.py`)* | `ArcadeUI` + `GameWindow` |
| `assets/fonts/Inter.ttf` | kept |

Renames: `PygameUI`→`ArcadeUI`, `pygame_input_handler.py`/`PygameInputHandler`→
`arcade_input_handler.py`/`ArcadeInputHandler`. Updated in `entrypoint.py`,
`src/ui/__init__.py`, `src/input_handler/__init__.py`.

## Key implementation notes

- **Coordinates.** Arcade is bottom-left y-up. All layout + hit-testing stay in top-left
  `Rect`s; `Painter` flips to GL only at the draw boundary; incoming mouse y is flipped
  once. Flipping the *projection* would mirror text, so it is not used.
- **Rounded rects.** Arcade 3.x has no rounded-rect primitive; `Painter.round_rect` builds
  one from two center bars + four AA corner circles. Borders/rings draw a filled shape
  behind an inset fill (alpha-0 cannot cut a hole).
- **Background.** Vertical gradient via a cached `ShapeElementList` vertex-colored quad.
- **Text.** `Painter` caches `arcade.Text` objects by content (board labels are numerous;
  `draw_text` re-layout per call is the documented slow path).

## Design

Refined dark (see session mockups): navy gradient bg; soft-shadowed layered cards with a
section color chip + accent bar; crisp AA boxes (crossed = ✕, circled = mint ring); dice
as rounded tiles with pips + gold selectable ring/glow; mint score / gold prompt; Inter
type ramp. Won-actions fold into the top resource rail + transient toasts (grey-card upper
band); the action legend moves into the `?` help overlay.

Interaction preserved + sharpened: click-a-die-to-pick (active→color, passive→index),
number keys, `H` hint, `?` help, `F11` fullscreen, `Esc` quit, resize reflow, button
hover/press states.

## Testing

Pure-logic tests are the CI signal: layout bounds/non-overlap/min-clamp/toast-slots,
`Rect` geometry, pick-map, animation easing/expiry, theme font-fallback + color math, pip
geometry. The headless render smoke test runs against an invisible Arcade window and
**skips when no GL context is available** (CI without a display) — replacing the old
SDL-dummy PNG dump. 480 tests pass; pylint 10.00/10; flake8 clean. End-to-end verified by
driving a full automatic game through `ArcadeUI` headlessly to GAME OVER.

## Dependencies

`setup.py` `interactive` extra: `arcade>=3.1,<4` (drops pygame). `.pylintrc`:
`extension-pkg-allow-list=arcade`; `max-args`/`max-positional-arguments` 8→9, `max-locals`
15→18, `min-public-methods=1` — accommodating coordinate-dense drawing primitives (mirrors
the existing `max-attributes=9`).

## Out of scope (unchanged)

1. Legal-placement highlighting (needs the board to expose valid targets per prompt).
2. Full die slide-across-panels positional tweens (kept to pick pulse + score ease).
