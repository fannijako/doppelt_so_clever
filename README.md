# Doppelt so clever

## Project Overview

A Python simulation of **Doppelt so clever** (*Twice as Clever*), the popular roll-and-write dice game. The game can be played interactively via the command line, through a Pygame UI, or run in fully automatic mode with randomized decisions.

### Game Mechanics

- **6 active rounds**, each consisting of up to **3 dice-picking turns**
- **6 dice** (green, blue, white, yellow, grey, pink) are rolled each turn
- Picking a die discards all dice with a lower value
- The **white die** acts as a wildcard and can substitute for any other color
- A **board** with 5 colored scoring sections (blue, pink, green, yellow, grey)
- **Special actions**: reroll, reuse a discarded die, +1 to a die, and color-specific question marks
- **Fox** bonuses multiply the lowest-scoring board section
- Final score is calculated by summing all board sections plus fox bonuses

## Project Structure

```
src/
├── entrypoint.py        # CLI argument parsing and logging setup
├── game/
│   ├── game.py          # Main game loop (6 active rounds)
│   ├── game_observer.py # Observer ABC for game events
│   ├── logging_observer.py    # Logging-only observer
│   └── composite_observer.py  # Multicasts to multiple observers
├── ui/
│   ├── pygame_ui.py     # Pygame observer, threading, input bridging
│   ├── renderer.py      # Pure rendering logic (draws board, dice, prompts)
│   ├── render_snapshot.py # Immutable dataclass snapshot of game state
│   └── constants.py     # Colors, dice colors, action labels, FPS
├── input_handler/
│   ├── base_input_handler.py      # InputHandler ABC
│   ├── consol_input_handler.py    # Console (stdin) input
│   ├── automatic_input_handler.py # Random/automatic input
│   ├── pygame_input_handler.py    # Delegates input to PygameUI
│   └── heuristics/                # Heuristic-based handlers
├── board/
│   ├── board.py         # Board with 5 colored parts and scoring
│   ├── board_parts/     # Blue, pink, green, yellow, grey board sections
│   └── boxes/           # Individual box logic per color
├── dice/
│   ├── dice.py          # Dice rolling and value management
│   └── dice_color.py    # Color enum (green, blue, white, yellow, grey, pink)
├── actions/
│   ├── action_handler.py        # Executes and chains actions
│   ├── action_type.py           # Action type enum
│   ├── immediate_actions/       # Actions resolved immediately
│   └── not_immediate_actions/   # Reroll, reuse, plus-one (saved for later)
└── round/
    ├── active_round.py  # Active round: dice picking, action resolution
    └── passive_round.py # Passive round: pick from lowest 3 dice
```

## Requirements

- Python >= 3.10

## Installation

1. Create a virtual environment:
```bash
make venv
source .venv/bin/activate
```

2. Install the package:
```bash
make build
```

3. Install test dependencies:
```bash
make build-test
```

4. Install interactive (Pygame) dependencies:
```bash
make build-interactive
```

5. Install RL training dependencies (PyTorch, TensorBoard):
```bash
make build-rl
```

## Usage

Run the game in **console mode** (prompts for dice choices via stdin):
```bash
make run
```

Run the game in **automatic mode** (random decisions):
```bash
make run-auto
```

Run the game in **interactive mode** (Pygame UI):
```bash
make run-interactive
```

Run the **Monte Carlo simulation**:
```bash
make run-monte-carlo
```

Train the **RL agent** (PPO):
```bash
make train-rl
```

Monitor training with **TensorBoard**:
```bash
tensorboard --logdir runs
```

All modes can be selected via the `--mode` flag:
```bash
python main.py --mode console          # default, stdin prompts
python main.py --mode automatic         # random decisions
python main.py --mode always-accept     # heuristic: always accept
python main.py --mode model             # trained model
python main.py --mode interactive       # Pygame UI
```

Enable verbose logging with the `-v` flag:
```bash
python main.py --mode automatic -v
```

## Development

Run tests:
```bash
make test
```

Run linters (pylint + flake8):
```bash
make lint
```
