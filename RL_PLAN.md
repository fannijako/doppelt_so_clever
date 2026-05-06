# Reinforcement Learning Plan — Doppelt so clever

## Goal

Train an RL agent to play the solo variant of Doppelt so clever, maximising the final score (sum of 5 board sections + fox bonuses). The agent replaces the `InputHandler` and makes every decision the game asks for: which die to pick, where to place it, whether to use reroll/reuse/plus-one actions, and how to resolve question-mark bonuses.

---

## 1 — State Representation

### 1.1 Board tensor (`Board.to_tensor()`)

Flatten `Board.to_dict()` into a fixed-size float vector. Proposed layout (all values normalised to [0, 1]):

| Section | Features per box | # Boxes | Total |
|---------|-----------------|---------|-------|
| Blue | `value_used / 12`, `max_limit / 12`, `is_filled` | 12 | 36 |
| Green | `value_used / 36`, `multiplier / 6`, `is_filled` | 12 | 36 |
| Pink | `value_used / 6`, `filter_limit / 6`, `is_filled` | 12 | 36 |
| Yellow | `value / 6`, `row / 4`, `col / 3`, `circled`, `crossed` | 10 | 50 |
| Grey | `color_onehot(6)`, `number / 6`, `crossed` | 24 | 192 |
| Yellow row/col actions | `available` flag | 9 | 9 |
| Grey col actions | `available` flag | 6 | 6 |
| Resources | `foxes / 6`, `gained_rerolls / 6`, `usable_rerolls / 6`, `gained_reuses / 6`, `usable_reuses / 6`, `gained_plus_ones / 6`, `usable_plus_ones / 6` | — | 7 |

**Estimated state vector size: ~372 floats** (exact count will be finalised during implementation).

### 1.2 Context features (appended to board tensor)

| Feature | Size |
|---------|------|
| Current round (1-6) / 6 | 1 |
| Current subround (1-3) / 3 | 1 |
| Active vs passive flag | 1 |
| Dice values (6 dice, each / 6) | 6 |
| Dice availability mask (6 binary) | 6 |
| Decision type one-hot (`choose_index`, `confirm`, `choose_value`) | 3 |
| Number of options available | 1 |

**Context size: ~19 floats → total input ≈ 391 floats.**

### 1.3 Implementation

Add `Board.to_tensor() -> list[float]` that converts `to_dict()` output into the flat numeric vector described above.

---

## 2 — Action Space

The game asks for decisions through three `InputHandler` methods. Each maps to a discrete action:

| Method | Semantics | Action space |
|--------|-----------|-------------|
| `choose_index(prompt, options)` | Pick one of N options | Discrete(N), N varies (max ~24 for grey question mark) |
| `confirm(prompt)` | Yes / No | Discrete(2) |
| `choose_value(prompt, valid_values)` | Pick a string from a list | Discrete(N), N varies (max 6 for die colors) |

### Variable-size action space handling

Use a **fixed-size output head** (e.g. 30 logits) and an **action mask**: set logits for invalid indices to -∞ before softmax. This is standard for masked PPO/A2C.

---

## 3 — Reward Design

| Signal | Value | When |
|--------|-------|------|
| **Terminal reward** | `board.evaluate()` (final score) | `on_game_ended` |
| **Intermediate shaping (optional)** | Delta in estimated board score after each `on_board_updated` | After each placement |

Start with **terminal-only reward** for simplicity. Add shaping later if training is slow to converge.

---

## 4 — Architecture Overview

### 4.1 Integration approach: `RLInputHandler` + `RLObserver`

This is the least invasive approach — no changes to `Game`, `ActiveRound`, or `PassiveRound`.

```
Game
 ├── RLObserver (GameObserver)  ← captures state, feeds it to the agent
 └── RLInputHandler (InputHandler) ← queries the policy network for actions
```

#### `RLObserver(GameObserver)`

- Tracks round/subround/phase context.
- On `on_dice_rolled`: stores current dice values.
- On `on_board_updated`: snapshots the board state via `Board.to_tensor()`.
- On `on_game_ended(score)`: stores terminal reward.
- Exposes `get_state() -> Tensor` to the input handler.

#### `RLInputHandler(InputHandler)`

- Holds a reference to the `RLObserver` and the policy network.
- On each `choose_*` / `confirm` call:
  1. Gets current state from the observer.
  2. Builds context features (decision type, option count, etc.).
  3. Feeds state to the policy → gets action logits.
  4. Applies action mask for valid options.
  5. Samples action (training) or takes argmax (evaluation).
  6. Stores the transition `(state, action, log_prob)` in a trajectory buffer.

### 4.2 Policy network

```
Input (391) → Linear(256) → ReLU → Linear(128) → ReLU →
  ├── Policy head → Linear(30) → masked softmax → action distribution
  └── Value head  → Linear(1) → state value (for PPO advantage estimation)
```

Framework: **PyTorch** (lightweight, well-supported PPO implementations available).

---

## 5 — Training Algorithm

**PPO (Proximal Policy Optimisation)** — standard for discrete-action, episodic environments.

### Hyperparameters (starting point)

| Param | Value |
|-------|-------|
| Learning rate | 3e-4 |
| Gamma (discount) | 0.99 |
| GAE lambda | 0.95 |
| Clip epsilon | 0.2 |
| Epochs per batch | 4 |
| Batch size | 64 episodes |
| Max training episodes | 500,000 |
| Entropy coefficient | 0.01 |
| Value loss coefficient | 0.5 |

### Training loop (high level)

```
for iteration in range(num_iterations):
    trajectories = []
    for _ in range(batch_size):
        board = Board()
        observer = RLObserver(board)
        handler = RLInputHandler(observer, policy)
        game = Game(handler, board, observer, ActionHandler(board))
        score = game.play()
        trajectories.append(handler.get_trajectory())

    advantages = compute_gae(trajectories)
    update_policy_ppo(policy, trajectories, advantages)
    log_metrics(iteration, scores)
```

---

## 6 — Implementation Phases

### Phase 1: State & action infrastructure
- [x] Implement `Board.to_tensor()` — flat numeric vector from `to_dict()`.
- [x] Create `RLObserver(GameObserver)` — tracks round context, dice, board snapshots.
- [x] Create `RLInputHandler(InputHandler)` — queries policy, records transitions.
- [x] Add `torch` and `numpy` to `setup.py` extras (`rl` extra).
- [x] Unit-test `to_tensor()` output shape and value ranges.

### Phase 2: Policy network & PPO core
- [x] Implement `PolicyNetwork(nn.Module)` with shared trunk, policy head, value head.
- [x] Implement action masking utility.
- [x] Implement trajectory buffer and GAE advantage computation.
- [x] Implement PPO update step (clipped surrogate loss + value loss + entropy bonus).
- [x] Unit-test PPO update with dummy data.

### Phase 3: Training script
- [x] Create `train_rl.py` (top-level, like `monte_carlo.py`).
- [x] Wire up the training loop: run N episodes → collect trajectories → PPO update.
- [x] Add logging: mean/max/min score per batch, loss components, entropy.
- [x] Add periodic model checkpointing (save to `model/checkpoints/`).
- [x] Add TensorBoard or Weights & Biases integration for monitoring.
- [x] Add `Makefile` target: `make train-rl`.

### Phase 4: Evaluation & baselines
- [ ] Run baseline Monte Carlo with `AutomaticInputHandler` (random) — establish lower bound.
- [ ] Run baseline with `AlwaysAcceptInputHandler` — establish heuristic baseline.
- [ ] Compare trained agent score distribution against baselines.
- [ ] Plot learning curves (score vs. episode).

### Phase 5: Iteration & improvements
- [ ] Tune hyperparameters (learning rate, network size, entropy coefficient).
- [ ] Add intermediate reward shaping (delta score after each board update).
- [ ] Experiment with observation augmentation (encode prompt text, action descriptions).
- [ ] Try curriculum learning: train first on subsets of rounds.
- [ ] Explore self-play or population-based training for diverse strategies.
- [x] Add `--mode rl` to monte_carlo.py to load trained checkpoint and use RLInputHandler for inference.

---

## 7 — File Structure (new/modified)

```
model/
├── checkpoints/              # saved .pt files
├── model.py                  # update: load trained policy for inference
├── policy_network.py         # NEW: nn.Module (shared trunk + two heads)
├── trajectory_buffer.py      # NEW: stores (s, a, r, log_prob, value)
└── ppo.py                    # NEW: PPO update logic, GAE computation
src/
├── board/
│   └── board.py              # modify: add to_tensor()
├── game/
│   └── rl_observer.py        # NEW: RLObserver(GameObserver)
├── input_handler/
│   └── model/
│       ├── model_input_handler.py  # modify: wire to trained policy
│       └── rl_input_handler.py     # NEW: RLInputHandler(InputHandler)
train_rl.py                   # NEW: training entrypoint
setup.py                      # modify: add "rl" extras (torch, numpy, tensorboard)
Makefile                      # modify: add train-rl target
```

---

## 8 — Success Criteria

| Metric | Target |
|--------|--------|
| Mean score after training | > 200 (solo "You've been training!" tier) |
| Stretch goal | > 260 ("This can't be luck!" tier) |
| Beats random baseline | By ≥ 50% average score improvement |
| Beats always-accept heuristic | By ≥ 20% average score improvement |
| Training wall-clock time | < 12 hours on a single GPU / < 24 hours CPU-only |

---

## 9 — Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Variable action space causes instability | Action masking; fixed-size output head |
| Sparse terminal reward slows learning | Add intermediate reward shaping (Phase 5) |
| Game episode length varies (many decisions) | High GAE lambda (0.95); consider n-step returns |
| `InputHandler` API doesn't expose board state | `RLObserver` captures it; shared reference passed to `RLInputHandler` |
| Chain-reaction actions create long decision sequences | Cap max decisions per step; ensure trajectory buffer handles variable lengths |
| Overfitting to specific dice rolls | Large training episode count; entropy regularisation |
