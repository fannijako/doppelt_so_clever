# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
make build              # core package (editable install)
make build-test         # adds pytest, pylint, flake8
make build-rl           # adds torch, numpy, tensorboard
make build-interactive  # adds pygame
make build-all          # everything

# Run
python main.py                             # console mode (stdin prompts)
python main.py play --mode automatic       # random decisions
python main.py play --mode interactive     # Pygame UI
python main.py play --mode model           # trained model
python main.py monte-carlo -r 1000 --mode automatic
python main.py train                       # PPO training
python main.py pbt-train                   # Population-Based Training
python main.py evaluate -n 1000            # RL evaluation vs baselines

# Test
python -m pytest                           # run all tests
python -m pytest test/board/               # run a specific folder
python -m pytest test/board/test_board_to_tensor.py  # run a single file
python -m pytest --cov=src --cov-report=term-missing  # with coverage

# Lint
make lint   # pylint + flake8
```

## Architecture

### Game Engine

`Game` (`src/game/game.py`) orchestrates 6 active rounds each followed by a passive round. It depends on three collaborators injected at construction: a `Board`, a `GameObserver`, and an `InputHandler`. These three are always assembled together in `src/entrypoint.py` (for play modes) or in the respective `scripts/` file for training/evaluation/monte-carlo.

**Observer pattern** — `GameObserver` (ABC in `src/game/game_observer.py`) receives lifecycle events: `on_dice_rolled`, `on_die_picked`, `on_board_updated`, `on_action_executed`, `on_game_ended`, etc. `CompositeObserver` multicasts to multiple observers. Implementations: `LoggingObserver`, `RLObserver`, `PygameUI`.

**InputHandler pattern** — `InputHandler` (ABC in `src/input_handler/base_input_handler.py`) has three methods: `choose_index()`, `confirm()`, `choose_value()`. Implementations: `ConsoleInputHandler`, `AutomaticInputHandler`, `PygameInputHandler`, `RLInputHandler`, `ModelInputHandler`.

**Round types** — `ActiveRound` (`src/round/active_round.py`) runs up to 3 dice-picking turns; picking a die discards all lower-valued dice. `PassiveRound` (`src/round/passive_round.py`) picks from the 3 lowest available dice.

### Board

`Board` (`src/board/board.py`) aggregates five colored board parts (blue, green, grey, pink, yellow). Each board part manages its own boxes, validates dice placement, and returns earned `Action`s. `Board.to_tensor()` produces a normalized 372-float vector used as the RL state prefix.

### Action System

`ActionHandler` (`src/actions/action_handler.py`) executes actions recursively. **Immediate actions** (question marks) are used right away and can chain further actions. **Not-immediate actions** (reroll, reuse, plus-one, fox) are saved to the board for later use. `ActionMap` (`src/actions/action_map.py`) is a singleton registry mapping `ActionType` → class; it lazy-initializes to avoid circular imports.

### RL Pipeline

```
RLObserver  →  board tensor (372) + context tensor (19) = state (391)
RLInputHandler  →  queries PolicyNetwork, records Transition per step
PolicyNetwork  →  shared MLP trunk (391→256→128) + policy head (→30 logits) + value head (→1)
PPOTrainer  →  updates PolicyNetwork from TrajectoryBatch
```

`RLObserver` (`src/game/rl_observer.py`) tracks game context (round, subround, dice state) and exposes `get_state()`. With `augmented=True` it appends an 11-float `PromptType` one-hot (state grows to 402). **The `augmented` flag must match between training and inference** — checkpoints should store this metadata.

`RLInputHandler` (`src/input_handler/model/rl_input_handler.py`) builds action masks (max 30 actions) and records `Transition`s during training; recording is skipped in eval mode.

Training is CPU-only by design: the bottleneck is the Python game simulation, not the small MLP. Use `--num-workers N` for parallel episode collection.

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/train_rl.py` | PPO training loop with checkpointing, TensorBoard, optional LR decay, curriculum, early stopping |
| `scripts/pbt_train_rl.py` | Population-Based Training: multiple agents, exploit/explore, hyperparameter perturbation |
| `scripts/evaluate_rl.py` | Compares RL agent against random and always-accept baselines; `--ci` exits non-zero if RL is below always-accept |
| `scripts/monte_carlo.py` | Bulk simulation with configurable mode |

TensorBoard logs go to `runs/`, checkpoints to `model/checkpoints/` (standard) or `model/pbt_checkpoints/` (PBT).

## Code Conventions

From `.windsurfrules` and `.pylintrc`:
- No docstrings or comments — names should be self-explanatory.
- No file-level `# pylint: disable` — fix the underlying issue instead.
- Keep methods small; split large methods into smaller private helpers.
- One assert per test method.
- Shared fixtures belong in `conftest.py`, not repeated in test files.
- Max line length: 127. Max class attributes: 9.
