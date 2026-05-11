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
│   ├── model_advisor.py # Loads trained model and provides action recommendations
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

### Local Installation

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

### Docker Installation

Build the Docker image:
```bash
make docker-build
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

Press **H** during any prompt to get a recommendation from the trained RL model (loaded from `model/pbt_checkpoints/best_agent.pt`). The recommended option will be highlighted with a cyan border.

Run the **Monte Carlo simulation**:
```bash
make run-monte-carlo
```

Run Monte Carlo with a **trained RL model**:
```bash
python main.py monte-carlo --mode rl --rounds 1000
```

Train the **RL agent** (PPO):
```bash
make train-rl
```

Train with **parallel episode collection** (uses multiple CPU cores):
```bash
python main.py train --num-workers 4
```

Train with **early stopping** (stops when score plateaus, restores best weights):
```bash
python main.py train --early-stop-patience 300 --early-stop-smoothing 0.05
```

Evaluate the **RL agent** against baselines (random, always-accept):
```bash
make evaluate-rl
```

Run evaluation with **CI gate** (exits non-zero if RL agent scores below Always-Accept):
```bash
python main.py evaluate -n 200 --ci --checkpoint model/ci_checkpoint.pt
```

Train the RL agent with **Population-Based Training** (PBT):
```bash
python main.py pbt-train --population-size 8 --iterations 5000 --num-workers 4
```

Run PBT training with **Docker** (default 5 iterations):
```bash
make docker-run
```

Override the number of iterations or parallel workers:
```bash
make docker-run ITERATIONS=1000
make docker-run NUM_WORKERS=8
```

Clean up Docker resources:
```bash
make docker-clean
```

Monitor training with **TensorBoard**:
```bash
tensorboard --logdir runs
```

---

## PBT Training Parameters

Population-Based Training runs multiple agents in parallel, periodically replacing the worst performers with mutated copies of the best. This automates hyperparameter tuning during training.

### PBT Schedule Parameters

| Parameter | Flag | Default | Effect |
|-----------|------|---------|--------|
| **population_size** | `--population-size` | 8 | Number of agents trained in parallel. Larger populations explore more hyperparameter combinations but increase compute linearly. |
| **iterations** | `--iterations` | 5000 | Total training iterations. Each iteration runs one PPO update per agent. More iterations give agents more time to converge. |
| **eval_interval** | `--eval-interval` | 50 | How often (in iterations) agents are evaluated and exploit/explore is triggered. Lower values adapt faster but add evaluation overhead. |
| **eval_episodes** | `--eval-episodes` | 32 | Number of game episodes used to estimate each agent's mean score. More episodes reduce variance in fitness estimation. |
| **batch_size** | `--batch-size` | 64 | Number of game episodes collected per agent per training step. Larger batches give more stable gradient estimates but slow each iteration. |
| **num_workers** | `--num-workers` | 0 (CLI) / 4 (Docker) | Number of parallel worker processes for episode collection. 0 means sequential. The Docker image defaults to 4 workers. Set to the number of CPU cores for best throughput. GPU is not used because the bottleneck is the Python game simulation, not the small neural network. |

### Exploit/Explore Parameters

| Parameter | Flag | Default | Effect |
|-----------|------|---------|--------|
| **fraction** | `--exploit-fraction` | 0.2 | Fraction of the population considered top/bottom performers. At each eval interval, the bottom fraction copies weights from a random top-fraction agent. Higher values are more aggressive (replace more agents). |
| **perturb_factor** | `--perturb-factor` | 1.2 | After copying weights, the new agent's learning rate and entropy coefficient are multiplied or divided by this factor (50/50 chance each). Larger values explore hyperparameter space more broadly; smaller values stay closer to proven configurations. |

### Per-Agent Hyperparameters (evolved by PBT)

| Parameter | Initial Range | Perturb Bounds | Effect |
|-----------|---------------|----------------|--------|
| **learning_rate** | log-uniform [1e-4, 1e-3] | [1e-6, 1e-2] | Controls the Adam optimizer step size. Too high → unstable policy updates; too low → slow learning. PBT adjusts this automatically. |
| **entropy_coefficient** | log-uniform [0.001, 0.05] | [1e-4, 0.1] | Weight of the entropy bonus in the PPO loss. Higher values encourage exploration (more random actions); lower values exploit the current best strategy. |
| **hidden1** | 256 (fixed) | — | First hidden layer size of the policy network. Not perturbed by PBT. |
| **hidden2** | 128 (fixed) | — | Second hidden layer size of the policy network. Not perturbed by PBT. |

### PPO Parameters (fixed across all agents)

| Parameter | Value | Effect |
|-----------|-------|--------|
| **clip_epsilon** | 0.2 | Clamps the policy ratio in the PPO surrogate objective. Prevents destructively large policy updates. |
| **epochs_per_batch** | 4 | Number of passes over the collected batch per PPO update. More epochs extract more signal from each batch but risk overfitting to stale data. |
| **value_loss_coefficient** | 0.5 | Weight of the value-function MSE loss relative to the policy loss. |
| **max_grad_norm** | 0.5 | Gradient clipping threshold. Prevents exploding gradients during optimization. |
| **minibatch_size** | 256 | Size of minibatches sampled from the batch during PPO updates. Smaller minibatches add noise that can help escape local optima. |

### I/O Parameters

| Parameter | Flag | Default | Effect |
|-----------|------|---------|--------|
| **checkpoint_dir** | `--checkpoint-dir` | `model/pbt_checkpoints` | Directory where the best agent is saved at the end of training. |
| **log_dir** | `--log-dir` | `runs/pbt` | TensorBoard log directory. Tracks per-agent learning rates, entropy coefficients, and population-level scores. |

All modes can be selected via the `--mode` flag:
```bash
python main.py play --mode console          # default, stdin prompts
python main.py play --mode automatic         # random decisions
python main.py play --mode always-accept     # heuristic: always accept
python main.py play --mode model             # trained model
python main.py play --mode interactive       # Pygame UI
```

Monte Carlo simulation modes:
```bash
python main.py monte-carlo --mode automatic         # random decisions
python main.py monte-carlo --mode always-accept     # heuristic: always accept
python main.py monte-carlo --mode model             # trained model
python main.py monte-carlo --mode rl                # RL model (loads latest checkpoint)
python main.py monte-carlo --mode rl --checkpoint model/checkpoints/checkpoint_000009.pt  # specific checkpoint
```

Enable verbose logging with the `-v` flag:
```bash
python main.py play --mode automatic -v
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
