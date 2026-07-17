# RL Tail Plan — driving sub-140 games toward zero

Goal set 2026-07-16 after run D (PR #41): mean 152.7 but **28.8% of games score
under 140** (p10=117, p5=106, p1=89, min=68 over 500-game diagnostic). Target:
0% under 140 at n=1000.

Companion to [`RL_PLATEAU_DIAGNOSIS.md`](./RL_PLATEAU_DIAGNOSIS.md) (mean-plateau
analysis); this doc targets the **left tail**.

## Evidence — what a sub-140 game looks like (500 games, run D best.pt, argmax)

| Metric | tail (<140, n=146) | good (≥140, n=354) | delta |
|---|---|---|---|
| score | 121.9 | 164.8 | +42.9 |
| **yellow** | **67.1** | **98.7** | **+31.5** |
| blue | 13.8 | 17.6 | +3.8 |
| green | 13.8 | 16.4 | +2.6 |
| pink | 11.0 | 12.8 | +1.8 |
| grey | 13.7 | 13.9 | +0.2 |
| min section | 6.8 | 8.2 | +1.4 |
| foxes | 0.38 | 0.67 | +0.29 |
| fox=0 games | 62% | 34% | — |

**73% of the tail gap is the yellow section alone.** Yellow's triangular payoff
(…55, 75, 96, 118, 141…) means one or two missing crosses cost 20–45 points.
Foxes correlate but are worth little today (0.5 foxes × min-section ≈7 ≈ 3.5 pts).
Leftover resources are equal (~1.8) in both groups — waste is not the mechanism.

## Feasibility calibration — be honest about "zero"

0/1000 under 140 requires p0.1 ≥ 140. Today median=152: the *median* game is
barely above the floor we want for the *worst* game. That means either mean
~190–210 with today's σ≈25, or a dramatic variance cut. Dice variance sets a
floor we can't shape away entirely. **Interim gates below are the real targets;
"literal zero" gets a go/no-go decision at Phase 3 with data.**

## Phase 0 — tail visibility (½ h)

`evaluate_rl.py`: add p10 / p5 / p1 / min and %<140 to the comparison table.
`train_rl.py`: raise `--eval-episodes` default for tail work (32 → 128; at 32,
p10 is ±1 category of noise) and select best.pt by **p10, not mean** behind a
flag (`--best-metric {mean,p10}`).
**Gate:** tail metrics visible in eval output; best.pt selection tail-aware.

## Phase 1 — tail-weighted fine-tune (warm start run D, ~2–4 h)

Three candidate mechanisms, in order of preference:

1. **Hinge terminal penalty** (recommended first): terminal reward
   `+= λ · min(0, score − 140) · terminal_scale`; new `--reward-mode` variant
   composable with `min-section`. Directly encodes the goal; trivial in
   `reward_shaper.py`. Risk: sparse signal, may need λ sweep {0.5, 1, 2}.
2. **Yellow-depth PBRS**: potential on yellow crossed-count (the observed
   mechanism, dense signal). Risk: over-fits yellow, starves other sections —
   the same failure class `total` shaping had.
3. **CVaR batch weighting**: upweight worst-q episodes per PPO batch (trainer
   change, no reward change). Cleanest theory, most code.

Start with (1); fall back to (2) if %<140 hasn't moved after ~1500 iters;
(3) only if both fail.
**Gate:** %<140 ≤ 15% and p5 ≥ 120 at n=1000, mean not regressing below 150.

## Phase 2 — capacity + exploration (fresh run, overnight)

Only if Phase 1 plateaus above its gate. 512/256 trunk (no warm start across
architecture), `--lr-decay`, higher early entropy; or PBT with exploit metric
switched from mean to p10. Cost: full retrain, ~8–12 h CPU.
**Gate:** %<140 ≤ 5% and p1 ≥ 130 at n=1000.

## Phase 3 — go/no-go on literal zero

If %<140 is ≤ 5% but p0.1 stalls under 140: quantify the dice-variance floor
(play the frozen policy on fixed seeds vs shuffled seeds; variance that persists
across policy improvements is luck, not skill) and either accept a revised
target (e.g. ≤ 0.5% under 140, p5 ≥ 145) or continue to bigger models.

## Non-goals

- No engine changes — engine is post-#40 correct and gated by faithfulness tests.
- No new observation features until Phase 2 evidence demands them
  (checkpoint-parity contract cost).
