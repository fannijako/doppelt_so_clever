# RL Plateau — Root-Cause Diagnosis

Why the trained agent stalls at ~108–116 mean and can't reach the higher score
categories (140+ / 160+) even after days of training.

Companion to [`RL_TRAINING_JOURNEY.md`](./RL_TRAINING_JOURNEY.md) — that doc logs
*what was tried*; this one identifies *why it caps*.

## TL;DR

The agent is trapped in a **shallow, breadth-first local optimum** that farms the
three cheap single-die sections (green / grey / pink) and abandons the two
sections that gate high scores (blue, yellow). The fox multiplier — the engine to
200+ — is effectively dead for every agent. The plateau is a reward/exploration +
observation problem, not "undertrained".

## Scoring structure

Final score = `Σ(5 sections) + foxes × min(section)`.

| Section | Payoff shape | Max | Cost per box |
|---|---|---|---|
| blue | triangular (0,1,3,6,10,…,78) | 78 | **blue die + white wildcard** (2 dice) |
| yellow | triangular (0,3,10,21,…,165) | 165 | **circle then cross** (2 matching dice) |
| grey | 4 × (0,2,4,7,11,16,22) | 88 | 1 die, needs full color rows |
| pink | linear sum of dice values | ~50 | 1 die |
| green | Σ(even-idx) − Σ(odd-idx), fills L→R | ~84 | 1 die |

Dice budget ≈ 24 base placements/game (6 rounds × [3 active + 1 passive]),
extended by question-marks / plus-ones / reuses / rerolls. You **must** concentrate.

## Evidence

### Per-section breakdown of `best.pt` (iter 1549, no-shaping, argmax, 300 games)

```
TOTAL  mean=108.4  median=108  max=153  std=16.4   foxes/game=0.6
  green   46.9   ← everything gets dumped here
  grey    33.1
  pink    17.6
  blue     5.9   ← ~3 of 12 boxes; triangular tail never reached
  yellow   3.3   ← ~1 crossed box
min section = yellow 68% / blue 29% / pink 2% / green 0.3%
fox bonus contribution = 1% of total
>=140: 3.0%   >=160: 0.0%   >=180: 0.0%
```

### Baseline cross-check (per-section means)

```
Random         total= 29.8  foxes=0.02 | blue= 4.8 pink=10.7 green= 2.6 yellow= 2.2 grey= 9.5
Always-Accept  total= 52.7  foxes=0.04 | blue= 9.2 pink=16.5 green= 4.8 yellow= 4.8 grey=17.4
Greedy         total= 55.7  foxes=0.02 | blue= 6.3 pink=10.0 green= 3.0 yellow= 1.5 grey=34.9
Fox-Balancing  total= 50.9  foxes=0.05 | blue= 9.1 pink=12.1 green= 7.8 yellow= 8.4 grey=13.4
```

- **Every agent — including the fox-targeting heuristic — gets ≈0 foxes.**
- The RL agent's green (46.9) is anomalous vs heuristics (3–8): it discovered a
  green-farm no heuristic uses, and sacrifices blue/yellow to do it.

### TensorBoard signatures

- **Shaped runs (default):** entropy collapses to ~1e-10, `score/mean` caps ~80.
- **No-shaping runs:** entropy stays healthy (~0.27), `score/mean` climbs to ~116
  then decelerates; `score/max` reached **178–184** in individual batches.

`score/max` ≈ 184 proves 160–180 is reachable within the dice economy — the
ceiling is the policy converging to green-farming under argmax, not the game.

## Root cause

The agent farms **cheap, single-die, immediate-payoff** sections (green/grey/pink)
and abandons **expensive, multi-step, delayed-payoff** sections (blue costs the
white wildcard; yellow needs two matching dice per box). This is locally rational
but structurally excludes every high-score pathway:

1. **The triangular tail is where big points live** (blue 8 boxes = 36, yellow 6
   crossed = 75). Reaching it needs sustained commitment the sparse terminal
   reward can't credit across ~30–50 decisions. Single-step entropy exploration
   never stumbles onto the circle→cross or fill-9-blue-boxes sequences.
2. **The fox multiplier is dead.** `foxes × min(section)` is the engine to 200+,
   but fox actions sit on *deep* boxes (blue box #9, pink box #8, a full grey /
   yellow column) that shallow play never reaches, and the min section sits at ~3
   so foxes would multiply almost nothing anyway. Mechanism is fine
   (`FoxAction.save` increments `board.foxes`) — it's starved by shallow play, and
   possibly a game-balance divergence from the physical game where foxes are central.

## Compounding factors (ranked)

1. **Observation gap (highest leverage).** The state encodes raw per-box fill
   flags but **not** the 5 per-section scores, the min-section, or per-section
   fox distance. (Correction: fox *count* is present — `to_tensor()` emits
   `foxes/6.0`; the original claim that it was absent is drift.) The
   256→128 MLP must re-derive the whole weakest-link objective (5 nonlinear
   section curves + their min + the multiplicative fox term) from raw flags — it
   can't, so critic values are noisy and the policy defaults to the
   highest-frequency signal (green). *Resolved by Phase 1:
   `board.strategic_features()` appended behind the `strategic_features` flag
   (state 762 → 778).*
2. **Shaping is ON by default and harmful.** `--shaped-rewards` defaults `True`
   (`python main.py train` / `make docker-run` use it). Shaped runs collapse
   entropy to ~1e-10 and cap ~80 because rewarding "boxes filled" reinforces
   breadth-farming. The 108–116 results *require* the non-default
   `--no-shaped-rewards`. Training with defaults for days trains the collapsed policy.
   *Resolved by Phase 2: `--reward-mode {none,total,min-section}` defaults to
   `none`; the legacy total shaping is opt-in for ablation.*
3. **Green scoring exploit / possible bug.** Green scores
   `Σeven-idx − Σodd-idx` with forced L→R fill — half of every green placement
   *subtracts*. Confirm this alternating rule is intended vs the real game's
   cumulative track. *Resolved by Phase 0: faithful — the rulebook's pairwise
   `first − second` star rule is exactly this alternating sum
   ([`PHASE0_ENGINE_FAITHFULNESS.md`](./PHASE0_ENGINE_FAITHFULNESS.md)). The
   green-farm is a legal exploit of a faithful rule, not a bug.*
4. **Capacity + flat option block.** 360 of 762 input dims are a
   positionally-flattened 30×12 option block; a 2-layer MLP can't cleanly attend
   over a variable option set for combinatorial planning. Secondary.

Minor: `CLAUDE.md` documented the augmented state as **402**; it was actually
**762** (option features added later). Doc drift — fixed; `CLAUDE.md` now
documents 391/762/778 and the checkpoint parity contract.

## Recommended fixes (leverage order)

1. **Add derived strategic features to the observation** — the 5 current section
   scores, the min-section (one-hot + value), fox count, per-section distance to
   the next fox box (~15 floats). Directly targets the weakest-link objective.
   Retrain from scratch with `--no-shaped-rewards`. *Primary root-cause remedy,
   distinct from "train longer/bigger".*
2. **Potential-based shaping on `min(section)`, not total.** The failed Phase-2
   experiment shaped on *total* score (reinforces green-farming). A potential on
   the minimum section rewards balance and pushes toward the fox pathway; γ=1
   keeps it policy-invariant in theory.
3. **Confirm the fox / green economy is faithful to the real game.** ~0 foxes for
   all strategies is a game-implementation ceiling capping everyone — no RL fix
   reaches 200+ until foxes are attainable. *Resolved by Phase 0: engine faithful,
   foxes reachable (green box 6, yellow col 3, grey col 3; `best.pt` earns
   0.6/game). The starvation is policy-side shallow play, not an engine ceiling
   ([`PHASE0_ENGINE_FAITHFULNESS.md`](./PHASE0_ENGINE_FAITHFULNESS.md)).*
4. Bigger net / curriculum / PBT — helps capacity but won't alone escape the
   local optimum without #1.
