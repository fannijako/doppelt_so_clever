# Architecture Overview

This project is a simulation of the board game **Doppelt so clever** (Twice as Clever).

---

## Project Structure

```
src/
├── entrypoint.py          # CLI entry point
├── game/
│   ├── game.py            # Game orchestrator
│   ├── game_observer.py   # Observer ABC for game events
│   ├── logging_observer.py    # Logging-only observer
│   └── composite_observer.py  # Multicasts to multiple observers
├── ui/
│   └── pygame_ui.py       # Pygame observer + rendering (interactive mode)
├── input_handler/
│   ├── base_input_handler.py      # InputHandler ABC
│   ├── consol_input_handler.py    # Console (stdin) input
│   ├── automatic_input_handler.py # Random/automatic input
│   ├── pygame_input_handler.py    # Delegates input to PygameUI
│   └── heuristics/                # Heuristic-based handlers
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
| *(module)* `entrypoint` | `src/entrypoint.py` | Parses CLI args (`-v`, `--mode`), builds observer + input handler, starts a `Game` | `Game`, `CompositeObserver`, `LoggingObserver`, `PygameUI`, `PygameInputHandler` |
| `Game` | `src/game/game.py` | Runs 6 active rounds, each followed by a passive round; grants round-specific bonus actions; triggers final scoring; notifies `GameObserver` on lifecycle events | `Board`, `ActionHandler`, `GameObserver`, `ActiveRound`, `PassiveRound`, `ReRollAction`, `ReUseAction`, `PlusOneAction`, `BlackQuestionMarkAction` |
| *(module)* `monte_carlo` | `monte_carlo.py` | Runs Monte Carlo simulations with configurable rounds | `Game`, `LoggingObserver` |

### Observers

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `GameObserver` (ABC) | `src/game/game_observer.py` | Abstract interface for game event listeners: round start/end, dice rolled, die picked, board updated, action executed, game ended | `Dice` (type-check only) |
| `LoggingObserver` | `src/game/logging_observer.py` | Logs every game event via `GameLogger` | `GameObserver`, `GameLogger` |
| `CompositeObserver` | `src/game/composite_observer.py` | Multicasts every event to a list of child `GameObserver`s | `GameObserver` |
| `PygameUI` | `src/ui/pygame_ui.py` | Pygame-based observer; tracks dice/board state for rendering; provides `wait_for_input()` / `submit_input()` for synchronous input from the UI thread | `GameObserver`, `Board`, `pygame` |

### Input Handlers

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `InputHandler` (ABC) | `src/input_handler/base_input_handler.py` | Abstract interface: `choose_index()`, `confirm()`, `choose_value()` | — |
| `ConsoleInputHandler` | `src/input_handler/consol_input_handler.py` | Reads from stdin | `InputHandler` |
| `AutomaticInputHandler` | `src/input_handler/automatic_input_handler.py` | Returns random valid choices | `InputHandler` |
| `PygameInputHandler` | `src/input_handler/pygame_input_handler.py` | Delegates all input to `PygameUI.wait_for_input()` — blocks until the UI submits a result | `InputHandler`, `PygameUI` |
| `ModelInputHandler` | `src/input_handler/model/model_input_handler.py` | Uses a trained model for decisions | `InputHandler` |

### Rounds

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `ActiveRound` | `src/round/active_round.py` | Executes 3 pick-turns per active round: rolls dice, lets player pick a color, discards lower dice, dispatches placement to the board, and optionally uses reroll/reuse/plus-one actions between turns; notifies observer on dice rolled, die picked, board updated, action executed | `Board`, `ActionHandler`, `GameObserver`, `Dice`, `DiceColor`, `Action`, `ReRollAction`, `ReUseAction`, `PlusOneAction` |
| `PassiveRound` | `src/round/passive_round.py` | Rolls all dice, selects from the 3 lowest, dispatches placement to the board; notifies observer on dice rolled, die picked, board updated, action executed | `Board`, `ActionHandler`, `GameObserver`, `Dice`, `DiceColor`, `Action` |

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
| `Action` (ABC) | `src/actions/base_action.py` | Abstract base for all actions; defines `save()` and `use()` interface; holds `action_type` and `is_immediate` flag | `ActionType`, `Board` (type-check only) |
| `ActionType` | `src/actions/action_type.py` | Enum of all action types (reroll, reuse, plus_one, fox, 6 question marks, none) | — |
| `ActionMap` | `src/actions/action_map.py` | Singleton registry mapping `ActionType` → concrete `Action` class; lazy-initialized to avoid circular imports | `ActionType`, all concrete action classes |
| `ActionHandler` | `src/actions/action_handler.py` | Executes a list of actions recursively: processes immediate actions in order, saves non-immediate actions to the board, and appends any newly earned immediate actions to the queue | `Board`, `Action`, `ActionType` |

#### Immediate Actions (question marks — used right away)

| Class | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| `ImmediateActions` | `src/actions/immediate_actions/immediate_actions.py` | Abstract base for immediate actions; `save()` raises an error | `Action`, `ActionType`, `Board` |
| `BlackQuestionMarkAction` | `src/actions/immediate_actions/black_question_mark.py` | Lets the player choose any color question-mark action to execute | `ImmediateActions`, all color question-mark actions |
| `BlueQuestionMarkAction` | `src/actions/immediate_actions/blue_question_mark.py` | Creates optimal blue + white dice to fill the next blue box | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `GreenQuestionMarkAction` | `src/actions/immediate_actions/green_question_mark.py` | Creates a green die with value 6 or 1 depending on the sign of the next empty field | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `GreyQuestionMarkAction` | `src/actions/immediate_actions/grey_question_mark.py` | Picks an uncrossed grey box and crosses it | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `PinkQuestionMarkAction` | `src/actions/immediate_actions/pink_question_mark.py` | Creates a pink die with value 6 and adds it to the pink board part | `ImmediateActions`, `Board`, `Dice`, `DiceColor` |
| `YellowQuestionMarkAction` | `src/actions/immediate_actions/yellow_question_mark.py` | Lists all possible placements on the yellow grid and lets the player pick one | `ImmediateActions`, `Board`, `Dice`, `DiceColor`, `YellowBoardAction` |

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
main.py → entrypoint → Game
                          ├── GameObserver (ABC)
                          │     ├── LoggingObserver
                          │     ├── CompositeObserver → [GameObserver...]
                          │     └── PygameUI ← PygameInputHandler
                          ├── InputHandler (ABC)
                          │     ├── ConsoleInputHandler
                          │     ├── AutomaticInputHandler
                          │     ├── PygameInputHandler → PygameUI
                          │     └── ModelInputHandler
                          ├── Board
                          │     ├── BlueBoardPart  → BlueBox
                          │     ├── GreenBoardPart → GreenBox
                          │     ├── GreyBoardPart  → GreyBox
                          │     ├── PinkBoardPart  → PinkBox
                          │     └── YellowBoardPart → YellowBox
                          ├── ActionHandler → Action (ABC)
                          │                    ├── ImmediateActions
                          │                    │     ├── Black/Blue/Green/Grey/Pink/YellowQuestionMarkAction
                          │                    └── NotImmediateActions
                          │                          ├── ReRollAction
                          │                          ├── ReUseAction
                          │                          ├── PlusOneAction
                          │                          └── FoxAction
                          ├── ActiveRound ──→ GameObserver
                          └── PassiveRound ──→ GameObserver
```

Both `ActiveRound` and `PassiveRound` depend on `Board`, `ActionHandler`, `GameObserver`, `Dice`, and `DiceColor`. Board parts depend on their respective box classes, `ActionMap`, `Dice`, and `DiceColor`.
