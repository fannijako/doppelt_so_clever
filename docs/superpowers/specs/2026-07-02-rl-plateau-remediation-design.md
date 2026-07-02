# RL Plateau Remediation — Design

Companion to [`model/RL_PLATEAU_DIAGNOSIS.md`](../../../model/RL_PLATEAU_DIAGNOSIS.md)
(the *why*) and [`model/RL_TRAINING_JOURNEY.md`](../../../model/RL_TRAINING_JOURNEY.md)
(the *what was tried*). This doc is the *fix plan*.

## Objective

Escape the 108–116 mean plateau **and** unlock the 200+ fox pathway.

200+ is `foxes × min(section)` driven. If the engine does not actually permit
foxes (all four baselines earn ≈0), no RL change reaches 200+. Therefore
engine-faithfulness is a **hard gate**, not a parallel track: verify the game
implementation before spending multi-day CPU on retraining.

## Scope decisions (resolved)

1. **Phase 0 is a hard gate** — Phase 1+ do not start until the engine is
   confirmed faithful (or fixed and re-baselined). Rationale: an engine bug that
   changes the reward landscape would invalidate any retraining; multi-day CPU is
   the expensive resource to protect.
2. **Interim reward default = no-shaping.** Flip the current harmful
   `shaped_rewards=True` default to no-shaping immediately. Switch the default to
   min-section potential shaping only after Phase 3 validates it — do not ship an
   untested reward as the default.
3. **Derived features computed in `board.strategic_features()`**, reusing the same
   internals as `board.evaluate()`. Single source of truth → no train/serve skew.
   Rejected alternative: computing them observer-local, which drifts from
   `evaluate()`.

## Current-state anchors (verified in code)

- `board.evaluate()` (`src/board/board.py:229`) = `sum(part_values) + foxes * min(part_values)`.
  Section scores and the min are computed here; nowhere else.
- `board.to_tensor()` emits **raw per-box fill flags**, plus `foxes/6.0`
  (`src/board/board.py:200`). So fox *count* is already in the state — the
  diagnosis's "fox count absent" claim is partly inaccurate. What is genuinely
  absent: the 5 per-section **scores**, the **min-section**, and per-section
  **distance-to-next-fox-box**.
- `RLObserver.get_state()` (`src/game/rl_observer.py:132`) = `board.to_tensor()`
  + context (round/phase, dice values/availability, decision-type one-hot, prompt
  one-hot, flattened 30×12 option block). No derived strategic features.
- `green_board_part.evaluate()` (`src/board/board_parts/green_board_part.py:66`) =
  `Σ value_used at even index − Σ value_used at odd index`, trailing odd box
  dropped. Half of every green placement subtracts — the flagged possible bug.
- `shaped_rewards: bool = True` default (`scripts/train_rl.py:39`, `:522`). The
  108–116 results require the non-default `--no-shaped-rewards`.
- Reward plumbing exists: `RewardConfig` / `RewardShaper`
  (`src/game/reward_shaper.py`) + `NO_SHAPING_REWARD_CONFIG` in `train_rl.py`.
  Min-section shaping is a new reward mode, not new plumbing.
- Rulebook anchors in repo: `rulebook.pdf`, `RULES.md`.

## Phase 0 — Engine faithfulness (GATE)

Diff the implementation against `rulebook.pdf` / `RULES.md` for the three suspects.

- **Green scoring** — is the real rule a cumulative track, not `Σeven − Σodd`?
- **Fox reachability** — foxes ≈0 for all four baselines including the
  fox-targeting heuristic. Structurally unreachable (bug) or intended-rare?
- **Min-section economy** — is `foxes × min(section)` a live lever at all in the
  faithful game?

If a bug is found: fix the engine, then **re-baseline the four heuristics and
regenerate the per-section evidence** in `RL_TRAINING_JOURNEY.md` — the reward
landscape changed, so this must precede any retrain.

**Verify:**
- One unit test per section encoding its scoring straight from the rulebook.
- Baselines (`random`, `always-accept`, `greedy`, `fox-balancing`) re-run.
- fox>0 demonstrably achievable by at least one strategy, or documented as
  intended-rare with the rulebook citation.

## Phase 1 — Observation features (primary root-cause)

Add a derived strategic-features block (~15 floats) to the state:

- 5 per-section scores, each normalized by that section's own max.
- min-section value + one-hot (which section is the min).
- per-section distance-to-next-fox-box.

(Fox count already present in `to_tensor`; do not duplicate.)

**Where:** new `board.strategic_features()`, reusing `evaluate()` internals.
Appended in `RLObserver.get_state()` behind a feature-config flag, mirroring the
existing `augmented` pattern.

**Parity contract:** persist the feature-config in checkpoint metadata —
`augmented` flag, strategic-features version, and resulting input dim. On load,
**assert the checkpoint's config matches the runtime observer**; mismatch raises.
This permanently closes the 402/762-class silent-divergence footgun.

Input dim grows → old checkpoints incompatible → retrain from scratch (accepted).

**Verify:**
- Unit test: `strategic_features(board)` equals values recomputed from
  `evaluate()` internals on randomly filled boards.
- Load-time mismatch between checkpoint config and observer config raises.
- State-size test pins the new total input dim.

## Phase 2 — Reward redesign + default flip

- Add a third reward mode: **potential-based shaping on `min(section)`**.
  `Φ(s) = scaled min-section score`, `F(s,s') = γΦ(s') − Φ(s)`, `γ=1` →
  policy-invariant in theory. Rewards *balance* and pushes the fox pathway.
  Distinct from today's total-score shaping (farms breadth) and no-shaping.
- **Flip the harmful default** per scope decision 2: `shaped_rewards` no longer
  defaults to breadth-farming total-shaping.
- Update the curriculum guard (`train_rl.py:449`), which currently requires
  shaped rewards for its per-step signal, so it composes with the new mode.

**Verify:**
- Unit test: PBRS contributions telescope to ~0 over a full episode (invariance
  sanity).
- Reward mode selectable via CLI.
- Curriculum guard updated and tested against the new mode matrix.

## Phase 3 — Retrain + eval (concrete runs)

- **Run A:** no-shaping + new features, from scratch — isolates the observation fix.
- **Run B:** min-section PBRS + new features, from scratch — isolates the shaping fix.

**Eval gates** (`evaluate_rl`, ≥300 games, argmax) vs the `best.pt` 108.4 baseline:
- total mean, per-section means, min-section distribution, foxes/game, %≥140, %≥160.
- Success: blue/yellow means rise materially, %≥140 rises materially above 3.0%,
  and (if Phase 0 made foxes reachable) foxes/game exceeds the baseline.

**TensorBoard criteria:**
- entropy stays healthy (no collapse to ~1e-10).
- `score/mean` clears ~116.
- `score/max` *sustained* toward 160+ (not spiky single batches).

**Verify:**
- `evaluate_rl --ci` exits zero (RL above always-accept).
- Regenerated per-section evidence pasted into `RL_TRAINING_JOURNEY.md`.

## Phase 4 — Capacity (conditional)

Only if Phase 3 stalls below target. Candidates: bigger trunk, attention over the
30×12 option block, curriculum, PBT. Not started speculatively — capacity does not
escape a local optimum on its own (per diagnosis fix #4).

## Cross-cutting — doc drift

- Fix `CLAUDE.md` RL-pipeline sizes (states 391/402 → actual 762+N after Phase 1).
- Document the checkpoint-metadata parity contract in `CLAUDE.md`.
- Correct the diagnosis doc's own drifted claims (e.g. fox-count-absent).

## Out of scope

- New network architectures beyond Phase 4's conditional list.
- Changes to the game engine beyond faithfulness fixes surfaced in Phase 0.
- Reward modes beyond no-shaping and min-section PBRS.
