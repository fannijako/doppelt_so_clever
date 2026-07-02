# RL Training Journey

End-to-end log of the debugging and experimentation cycle that took the RL agent from worse-than-random to beating every heuristic baseline.

## Goal

Train an RL agent that can play Doppelt so clever competitively against heuristic baselines, with the long-term target of reaching a mean score of 160+ (matching strong human play).

## Starting point: total failure

The agent was scoring **9.9 mean** on 1000 episodes — significantly **worse than random (28.8)**.

```
Random           28.8 ± 9.3
Always-Accept    52.4
Greedy           55.6
Fox-Balancing    51.8
Resource-Aware   49.9
RL Agent          9.9 ± 6.3   ← worse than random
```

## Diagnostic process

### 1. TensorBoard log inspection

Initial 50–200 iter runs showed:
- `score/mean` starts near random (~30), then **collapses to ~10 within ~50 iters**
- `loss/entropy` decays from 1.0 → 0.15 quickly
- `eval/mean_score` flat at 10–12 for the entire run

This ruled out "just undertrained" — the agent was actively learning the wrong thing.

### 2. Reward flow audit

Traced the trajectory of reward signals from `RLInputHandler` → `RewardShaper` → `compute_gae` and discovered:

- **Shaping rewards** (per step): box(0.5), fox(1.0), plus_one(1.0), reroll(0.3), reuse(0.3), failed(-2.0) → cumulative ~15–30 per episode
- **Terminal reward**: `final_score × DEFAULT_TERMINAL_REWARD_SCALE` where the scale was `1/300` → for typical scores of 30–50, terminal contribution = 0.1–0.17

**The terminal reward was ~100× smaller than the shaping reward.** The agent was optimizing 100% for shaping signals and 0% for actual game score. The "bad" mode at score ~10 was actually *optimal* for the shaped objective — the agent was correctly solving the wrong problem.

## Three fixes that unlocked baseline-beating performance

| Fix | From | To | Why |
|---|---|---|---|
| `DEFAULT_TERMINAL_REWARD_SCALE` | 1/300 | **1/10** | Make terminal reward ~30% of total signal instead of 1%. The biggest lever. |
| `entropy_coef` | 0.01 | **0.05** | Larger entropy bonus relative to shaping magnitude keeps exploration alive long enough to find good strategies. |
| Reward shaping weights | flat | halved + split | Halve all weights; split so plus-ones/question-marks (0.5) > rerolls/reuses (0.15), fox (0.25). |

After ~1000 iters of training:

```
RL Agent  79.8 ± 16.3   ← +24 over Greedy, beats all heuristics
```

## Tooling added during the cycle

- **`scripts/monitor_rl.py`** + `make monitor-rl` target — polls the latest TB event file every 10 min (configurable) and prints a one-line snapshot of key scalars. Made it possible to babysit long runs without keeping TB open.

## Pushing further: Phase 1 (no-shaped-rewards from `best.pt`)

The 79.8 mean was 24 points above Greedy but still capped at heuristic-level play (`<140` for 100% of games). Hypothesis: **shaping rewards correlated with heuristic play and were now the cap**. Test: resume from `best.pt` with `--no-shaped-rewards` so the gradient came entirely from terminal score.

Result after ~900 more iters:

```
RL Agent  112.5 ± 16.7   ← +32.7 over previous, first time crossing 140 (4.6% of games)
```

Key milestones during Phase 1:
- `score/max` climbed from 131 → 172 (highest individual episode)
- Crossed Always-Accept (52) at iter 200
- Crossed Greedy (55) at iter 300
- Crossed 100 mean at iter ~1300

Entropy stayed healthy (0.30+) throughout — the policy was re-exploring, not converging. **Removing shaping from a competent policy unlocked strategic play that shaped rewards had suppressed.**

## Continued Phase 1 (extended)

Resumed again for 500 more iters at iter 2000. Slope decelerated significantly:

| Window | Slope (eval points / 100 iters) |
|---|---|
| iter 1100 → 1800 (Phase 1 main) | +4.3 |
| iter 1800 → 2400 (extended) | +0.5 (~10× decel) |

Best.pt reached eval 114.91 at iter 2150. Diminishing returns clearly setting in.

## Phase 2 attempt: partial-score shaping (failed)

Hypothesis: with shaping removed, sparse terminal-only signal struggles to credit individual actions. Replace shaping with a **potential-based** signal proportional to actual partial-score deltas (`use_partial_score=True`, `w_score=0.05`), which under γ=1 should preserve the optimal policy while accelerating learning.

**Result: regression.** In 150 iters:
- `score/mean` dropped 110.81 → 96.64 (−14)
- `score/max` dropped 153 → 125 (capability degraded, not just consistency)
- Three consecutive evals below 100

The partial-score shaping reoriented the policy toward greedy section-by-section accumulation, away from the multi-section strategic play Phase 1 had discovered. Even when "aligned" with the objective, dense shaping was capping the policy.

**Phase 2 reverted.** Reward shaper defaults restored to Phase 1 (extended) values. `best.pt` restored from `checkpoint_001799.pt`.

## Final standings

```
Random           30.2 ± 10.7
Resource-Aware   49.2
Fox-Balancing    51.9
Always-Accept    52.8
Greedy           55.2
RL Agent        112.5 ± 16.7   ← +273% over random, +104% over Greedy
```

Distribution: 95.4% of games <140, 4.4% in 140–159, 0.2% in 160–179. The agent can score in your target band but not consistently.

## Lessons

1. **Reward magnitude matters more than reward identity.** The terminal-reward fix (1/300 → 1/10) was the single biggest unlock — the signal existed but was drowned out.
2. **Watch entropy as the headline diagnostic.** Entropy crashing to ~0.15 within 50 iters is policy collapse; healthy decay stays above 0.20 for hundreds of iters.
3. **Heuristic-correlated shaping caps the policy at heuristic level.** Rewarding "boxes filled" / "resources collected" teaches the agent to play like the heuristics. Removing shaping after the agent is competent unlocks strategic play.
4. **Even theoretically-sound shaping can hurt.** Partial-score shaping (potential-based, γ=1, should preserve optimal policy) caused a regression in practice. The dense signal pulled the policy toward locally-greedy accumulation.
5. **Resume + `best.pt` has a subtle pitfall.** On resume, `best_eval_score` resets to `-inf`, so the first eval after resume overwrites `best.pt` even if it's worse than the previous best. Back up `best.pt` before any resume.
6. **Diminishing returns are real.** Phase 1 slope went from +4.3/100 to +0.5/100 over the same recipe. Pushing to 160 mean will likely require structural changes (larger network, curriculum, PBT), not more iters of the same.

## Reference: how to reproduce the best result

```bash
# Train from scratch with the current defaults
make docker-build
make docker-run ITERATIONS=2000 TRAIN_ARGS="--no-shaped-rewards"
make docker-evaluate EPISODES=1000

# Or restore from the saved checkpoint
cp model/checkpoints/checkpoint_001799.pt model/checkpoints/best.pt
make evaluate-rl
```

## What to try next for 160+

In order of expected leverage:

1. **Larger network** (`--hidden1 512 --hidden2 256`) — more capacity for multi-step planning. Fresh train + `--no-shaped-rewards`.
2. **PBT** with the no-shaping recipe — population-based hyperparameter exploration.
3. **Curriculum** (`--curriculum`) — train on 2-round games first, gradually scale to 6, with `--no-shaped-rewards`.
4. **Longer training** — accept diminishing returns and run 5000+ iters of `--no-shaped-rewards` overnight. Slope of +0.5/100 over 5000 iters gives +25 → ~137.

Avoid: re-introducing shaping of any kind, even potential-based. The Phase 2 result is the cautionary tale.
