# Pygame UI Upgrade — Design

**Date:** 2026-07-15
**Status:** Approved (direction + full scope confirmed)

## Goal

Upgrade the interactive UI's *presentation and interaction* while keeping pygame.
Touch only the view — `Game`, observers, threading, `InputHandler`, `RenderSnapshot`
are unchanged.

## Direction

Stay in pygame. The plumbing (observer pattern, game-thread/render-thread split via
lock + `threading.Event`, `RenderSnapshot`) is framework-agnostic and healthy. The
weakness is purely visual: `SysFont("monospace")`, flat palette, dice shown as numbers,
no motion, ~100 magic layout constants.

## Scope (all confirmed)

- **Reskin** — bundled Inter TTF (proportional), coherent dark palette with accessible
  contrast, dice drawn with **pips** (1–6; "?" for unrolled), rounded cards + drop
  shadow + per-section accent bar, consistent spacing.
- **Motion & feedback** — score-value easing, die-pick pulse/glow, hover + press button
  states, polished popup fade (generalizes today's popup timer).
- **Interaction** — **click a die to pick** (active round → color option; passive round →
  die-index option), `?` help overlay, hover highlight on options. Number keys / buttons
  still work.
- **Windowed + responsive** — default `1280×800` `RESIZABLE`, reflow on resize, `F11`
  fullscreen toggle (drops forced `FULLSCREEN`).

## Module layout (`src/ui/`)

| File | Responsibility |
|------|----------------|
| `theme.py` | `Theme` dataclass: semantic palette + font loader (bundled Inter → SysFont fallback) |
| `layout.py` | `Layout(width, height)` → rects for every region; scales from a base design size, clamps to minimums. Replaces `_calculate_panel_dimensions` + magic constants |
| `widgets.py` | primitives: `draw_card` (accent + shadow), `draw_die` (pips), `draw_button` (states), `draw_pill`, ease functions |
| `animations.py` | time-based transient tracker: score ease, die-pick pulse, popup fade |
| `renderer.py` | slimmed orchestrator; section drawers read `Layout`, not constants |
| `pygame_ui.py` | resizable window, `VIDEORESIZE`, `F11`, `?` overlay, click-to-pick hit-testing, score-ease state; threading/observer untouched |
| `constants.py` | shrinks to text maps only (`ACTION_LABELS`, `POPUP_*_NAMES`) |
| `assets/fonts/Inter.ttf` | bundled OFL font (variable, default = Regular) |

## Pick-click mapping

- Active round: `choose_value('Pick an available color')` → clicking a die submits the
  option index whose color matches the die.
- Passive round: `choose_index('Pick a die index')` → clicking a die submits its option
  index by identity.
- `confirm` / other `choose_value` prompts → buttons only (no die mapping).
- Buttons + number keys remain functional in every prompt as fallback.

## Tests (`test/ui/`, no display required)

Pure-logic: layout bounds / non-overlap / min-clamp; font fallback when asset missing;
pip positions per value 1–6; click→option mapping (color vs index); animation easing
convergence + popup expiry. Plus a **headless smoke test** (`SDL_VIDEODRIVER=dummy`)
rendering one full frame from a synthetic snapshot → asserts no exception and dumps a
PNG for visual verification.

## Out of scope (flagged)

1. **Legal-placement highlighting** — needs the board to expose valid targets per prompt
   (game-logic coupling, not a view change). Follow-up.
2. **Die slide-across-panels** — simplified to pick pulse + score ease; a full positional
   tween fights the snapshot model for little payoff.

## Defaults chosen

- Dark theme only (matches current background; less work than dual-theming).
- Bundled font with SysFont fallback so a missing asset degrades gracefully.
