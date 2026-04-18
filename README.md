# Doppelt so clever

## Project Overview

A Python simulation of **Doppelt so clever** (*Twice as Clever*), the popular roll-and-write dice game. The game can be played interactively via the command line or run in fully automatic mode with randomized decisions.

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
├── monte_carlo.py       # Monte Carlo simulation
├── game.py              # Main game loop (6 active rounds)
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
    └── active_round.py  # Round execution, dice picking, and action resolution
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

## Usage

Run the game in **interactive mode** (prompts for dice choices):
```bash
make run
```

Run the game in **automatic mode** (random decisions):
```bash
make run-auto
```

Run the **Monte Carlo simulation**:
```bash
make run-monte-carlo
```

Enable verbose logging with the `-v` flag:
```bash
python main.py -a -v
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
