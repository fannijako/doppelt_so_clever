# Architecture Overview

This project is a simulation of the board game **Doppelt so clever** (Twice as Clever).

---

## Project Structure

```
src/
├── entrypoint.py          # CLI entry point (supports -v, -a, -p flags)
├── monte_carlo.py         # Monte Carlo simulation
├── game.py                # Game orchestrator (CLI / automatic)
├── pygame_game.py         # Pygame-based interactive game (extends Game)
├── ui/
│   └── pygame_ui.py       # Pygame graphical UI renderer and input handler
├── dice/                  # Dice and color definitions
├── round/                 # Active and passive round logic
├── board/
│   ├── board.py           # Central board aggregator
│   ├── board_parts/       # Color-specific board sections
│   └── boxes/             # Individual box data models
└── actions/
    ├── base_action.py     # Abstract action base class
    ├── action_type.py     # Action type enum
    ├── action_map.py      # Action type → class registry
    ├── action_handler.py  # Recursive action executor
    ├── immediate_actions/  # Question-mark actions (used immediately)
    └── not_immediate_actions/  # Stored actions (reroll, reuse, etc.)
```

---

## Classes

### Entry & Orchestration

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| *(module)* `entrypoint` | `src/entrypoint.py` | Parses CLI args (`-v`, `-a`, `-p`), sets up logging, starts a `Game` or `PygameGame` | `Game`, `PygameGame` |
| `Game` | `src/game.py` | Runs 6 active rounds, each followed by a passive round; grants round-specific bonus actions; triggers final scoring | `Board`, `ActionHandler`, `ActiveRound`, `PassiveRound`, `ReRollAction`, `ReUseAction`, `PlusOneAction`, `BlackQuestionMarkAction` |
| *(module)* `monte_carlo` | `src/monte_carlo.py` | Runs Monte Carlo simulations with configurable rounds | `Game` |
| `PygameGame` | `src/pygame_game.py` | Extends `Game` with a pygame UI; overrides round execution, dice picking, placement, and action resolution to use graphical interaction via `PygameUI` | `Game`, `PygameUI`, `Board`, `ActionHandler`, `ActiveRound`, `PassiveRound`, `Dice`, `DiceColor`, `ReUseAction`, `PlusOneAction` |

### Rounds

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `ActiveRound` | `src/round/active_round.py` | Executes 3 pick-turns per active round: rolls dice, lets player pick a color, discards lower dice, dispatches placement to the board, and optionally uses reroll/reuse/plus-one actions between turns | `Board`, `ActionHandler`, `Dice`, `DiceColor`, `Action`, `ReRollAction`, `ReUseAction`, `PlusOneAction` |
| `PassiveRound` | `src/round/passive_round.py` | Rolls all dice, selects from the 3 lowest, dispatches placement to the board | `Board`, `ActionHandler`, `Dice`, `DiceColor`, `Action` |

### UI

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `PygameUI` | `src/ui/pygame_ui.py` | Renders the full game board, dice, actions, score, and round info in a pygame window; handles user input via clickable buttons and keyboard events; provides `wait_for_input()` for blocking UI choices | `Board`, `Dice`, `ActionType`, `pygame` |
| `GameState` | `src/ui/pygame_ui.py` | Enum tracking UI state: `WAITING_FOR_INPUT`, `ANIMATING`, `IDLE` | — |
| `Colors` | `src/ui/pygame_ui.py` | Constants class holding all UI color tuples and an action-type → color mapping | `ActionType` |

### Dice

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `Dice` | `src/dice/dice.py` | Represents a single die with a color and a rollable value (1–6) | `DiceColor` |
| `DiceColor` | `src/dice/dice_color.py` | Enum of the 6 dice colors: green, blue, white, yellow, grey, pink | — |

### Board

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `Board` | `src/board/board.py` | Aggregates all 5 colored board parts; tracks foxes, rerolls, reuses, plus-ones; handles white-dice substitution; computes final score via `evaluate()` | `BlueBoardPart`, `PinkBoardPart`, `GreenBoardPart`, `YellowBoardPart`, `GreyBoardPart`, `Dice`, `DiceColor`, `Action` |

### Board Parts

Each board part manages a list of color-specific boxes, validates dice placement, and returns earned `Action`s.

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `BlueBoardPart` | `src/board/board_parts/blue_board_part.py` | Stores 12 `BlueBox`es; placement uses sum of blue + white dice; each placement lowers the value limit for subsequent boxes; scoring via triangular-number map | `BlueBox`, `ActionMap`, `Dice`, `DiceColor`, `ActionType` |
| `GreenBoardPart` | `src/board/board_parts/green_board_part.py` | Stores 12 `GreenBox`es filled sequentially; dice value is multiplied by box multiplier; scoring alternates add/subtract pairs | `GreenBox`, `ActionMap`, `Dice`, `DiceColor`, `ActionType` |
| `GreyBoardPart` | `src/board/board_parts/grey_board_part.py` | 4 rows × 6 columns grid of `GreyBox`es; crosses boxes matching (color, number); white/grey dice are substituted to another color; completing a column grants an action | `GreyBox`, `ActionMap`, `Dice`, `DiceColor`, `ActionType` |
| `PinkBoardPart` | `src/board/board_parts/pink_board_part.py` | 12 sequential `PinkBox`es; stores the raw dice value; action is only granted if the value meets the box's filter limit; scoring is the sum of stored values | `PinkBox`, `ActionMap`, `Dice`, `DiceColor`, `ActionType` |
| `YellowBoardPart` | `src/board/board_parts/yellow_board_part.py` | 10 `YellowBox`es on a 5×4 grid; dice placement first circles, then crosses a box; completing a row or column grants an action; scoring via points map on number of crossed boxes | `YellowBox`, `YellowBoardAction`, `ActionMap`, `Dice`, `DiceColor`, `ActionType` |

### Boxes

Each box is a data model for a single cell on a board part.

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `BlueBox` | `src/board/boxes/blue_box.py` | Holds a maximum value limit and an action type; stores the sum of blue + white dice if within limit | `ActionType` |
| `GreenBox` | `src/board/boxes/green_box.py` | Holds a value multiplier, an action type, and an index; stores `dice_value × multiplier` | `ActionType` |
| `GreyBox` | `src/board/boxes/grey_box.py` | Holds a color and number (1–6); can be crossed when a matching die is placed | `DiceColor` |
| `PinkBox` | `src/board/boxes/pink_box.py` | Holds an action filter limit and an action type; stores the raw dice value | `ActionType` |
| `YellowBox` | `src/board/boxes/yellow_box.py` | Holds a value and grid position (row, column); supports two-stage marking: circle → cross | — |

### Actions

#### Base & Infrastructure

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `Action` (ABC) | `src/actions/base_action.py` | Abstract base for all actions; defines `save()` and `use()` interface; holds `action_type`, `is_immediate` flag, and an optional `pick_option_callback` for UI-driven option selection | `ActionType`, `Board` (type-check only) |
| `ActionType` | `src/actions/action_type.py` | Enum of all action types (reroll, reuse, plus_one, fox, 6 question marks, none) | — |
| `ActionMap` | `src/actions/action_map.py` | Singleton registry mapping `ActionType` → concrete `Action` class; lazy-initialized to avoid circular imports | `ActionType`, all concrete action classes |
| `ActionHandler` | `src/actions/action_handler.py` | Executes a list of actions: saves non-immediate actions first, then processes immediate actions in a loop; supports `pick_action_callback` and `pick_option_callback` for UI-driven selection; propagates `pick_option_callback` to each action before use | `Board`, `Action`, `ActionType` |

#### Immediate Actions (question marks — used right away)

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `ImmediateActions` | `src/actions/immediate_actions/immediate_actions.py` | Abstract base for immediate actions; `save()` raises an error | `Action`, `ActionType`, `Board` |
| `BlackQuestionMarkAction` | `src/actions/immediate_actions/black_question_mark.py` | Lets the player choose any color question-mark action to execute; propagates `pick_option_callback` to the chosen action; supports UI callback, CLI input, and automatic (random) modes | `ImmediateActions`, all color question-mark actions |
| `BlueQuestionMarkAction` | `src/actions/immediate_actions/blue_question_mark.py` | Creates optimal blue + white dice to fill the next blue box | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `GreenQuestionMarkAction` | `src/actions/immediate_actions/green_question_mark.py` | Creates a green die with value 6 or 1 depending on the sign of the next empty field | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `GreyQuestionMarkAction` | `src/actions/immediate_actions/grey_question_mark.py` | Picks an uncrossed grey box and crosses it; supports UI callback, CLI input, and automatic (random) modes | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `PinkQuestionMarkAction` | `src/actions/immediate_actions/pink_question_mark.py` | Creates a pink die with value 6 and adds it to the pink board part | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `YellowQuestionMarkAction` | `src/actions/immediate_actions/yellow_question_mark.py` | Lists all possible placements on the yellow grid and lets the player pick one; supports UI callback, CLI input, and automatic (random) modes | `ImmediateActions`, `Board`, `Dice`, `DiceColor`, `YellowBoardAction` |

#### Not-Immediate Actions (stored on the board for later use)

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `NotImmediateActions` | `src/actions/not_immediate_actions/not_immediate_actions.py` | Abstract base for stored actions | `Action`, `ActionType` |
| `ReRollAction` | `src/actions/not_immediate_actions/reroll_action.py` | `save()` increments `board.gained_rerolls` / `usable_rerolls` (grants `FoxAction` at 6); `use()` decrements `usable_rerolls` | `NotImmediateActions`, `Board`, `FoxAction` |
| `ReUseAction` | `src/actions/not_immediate_actions/reuse_action.py` | `save()` increments `board.gained_reuses` / `usable_reuses` (grants `PinkQuestionMarkAction` at 6); `use()` lets the player reclaim a discarded die | `NotImmediateActions`, `Board`, `Dice`, `PinkQuestionMarkAction` |
| `PlusOneAction` | `src/actions/not_immediate_actions/plus_one_action.py` | `save()` increments `board.gained_plus_ones` / `usable_plus_ones` (grants `GreyQuestionMarkAction` at 6); `use()` lets the player pick any previously-rolled die to place again | `NotImmediateActions`, `Board`, `Dice`, `DiceColor`, `GreyQuestionMarkAction` |
| `FoxAction` | `src/actions/not_immediate_actions/fox_action.py` | `save()` increments `board.foxes`; `use()` is forbidden | `NotImmediateActions`, `Board` |

---

## Dependency Diagram (high-level)

```
main.py → entrypoint → Game ──────────────────────────────────────┐
                    └──→ PygameGame (extends Game) → PygameUI       │
                          ├── Board                                 │
                          │     ├── BlueBoardPart  → BlueBox        │
                          │     ├── GreenBoardPart → GreenBox       │
                          │     ├── GreyBoardPart  → GreyBox        │
                          │     ├── PinkBoardPart  → PinkBox        │
                          │     └── YellowBoardPart → YellowBox     │
                          ├── ActionHandler → Action (ABC)          │
                          │     │  (pick_action_callback,           │
                          │     │   pick_option_callback)           │
                          │     ├── ImmediateActions                │
                          │     │     ├── Black/Blue/Green/Grey/Pink/YellowQuestionMarkAction
                          │     └── NotImmediateActions             │
                          │           ├── ReRollAction              │
                          │           ├── ReUseAction               │
                          │           ├── PlusOneAction             │
                          │           └── FoxAction                 │
                          ├── ActiveRound                           │
                          └── PassiveRound                          │
```

`PygameGame` extends `Game` and injects `PygameUI` for graphical rendering and input. It sets `pick_action_callback` and `pick_option_callback` on `ActionHandler`, which propagates `pick_option_callback` to each action before execution. Both `ActiveRound` and `PassiveRound` depend on `Board`, `ActionHandler`, `Dice`, and `DiceColor`. Board parts depend on their respective box classes, `ActionMap`, `Dice`, and `DiceColor`.
