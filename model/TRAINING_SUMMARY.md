# RL Training Summary

PPO training run that beat all heuristic baselines on Doppelt so clever.

## Setup

- 1000 iterations, batch size 64 episodes → ~64,000 training episodes
- CPU-only, single Docker container, ~2h 13min wall-clock
- `best.pt` selected by periodic 32-episode eval every 50 iters (Phase 5)

## Training trajectory (selected waypoints)

| Iter | score/mean | score/max | eval | entropy | Notes |
|---:|---:|---:|---:|---:|---|
| 16 | 22.7 | 34 | — | 0.69 | Early exploration — eval hasn't fired yet |
| 121 | 41.5 | 70 | 39.8 | 0.45 | First eval datapoint |
| 200 | 51.3 | 88 | **52.8** | 0.40 | Crossed Always-Accept baseline |
| 300 | 63.2 | 103 | **62.3** | 0.37 | Crossed Greedy baseline |
| 400 | 70.5 | 115 | 71.5 | 0.31 | First eval > 70 |
| 800 | 78.7 | 112 | **79.2** | 0.24 | `best.pt` checkpoint saved (peak eval) |
| 1000 | 74.5 | 122 | 75.0 | 0.26 | Final iteration |

## Entropy evolution

Entropy is the headline diagnostic for whether the policy is still exploring or has committed too early. This run kept exploration healthy throughout:

| Range | Entropy | Behavior |
|---|---|---|
| iter 0–50 | 1.00 → 0.70 | Near-uniform policy, mostly random sampling |
| iter 50–200 | 0.70 → 0.40 | Steepest learning phase — most of the score gain happens here |
| iter 200–600 | 0.40 → 0.30 | Gradual convergence, still ~30% of max entropy |
| iter 600–800 | 0.30 → 0.24 | Policy committing to a strategy, eval climbing |
| iter 800–1000 | 0.24 → 0.26 | Entropy bounced up slightly — late-stage re-exploration, not collapse |

The decay pattern is concave-down, never falling below 0.23.

## Final evaluation (1000 episodes)

| Agent | Mean | Std | Median | Max |
|---|---:|---:|---:|---:|
| Random | 30.2 | 10.8 | 29.0 | 75 |
| Resource-Aware | 49.7 | 12.7 | 49.0 | 98 |
| Fox-Balancing | 52.0 | 13.9 | 52.0 | 97 |
| Always-Accept | 52.5 | 13.9 | 52.0 | 107 |
| Greedy | 55.6 | 11.8 | 55.0 | 91 |
| **RL Agent** | **79.8** | **16.3** | **80.0** | **131** |

RL beats Greedy (the strongest heuristic) by **+24.2 points** and the random baseline by **+164%**. The RL agent's worst episode (min 34) is above the random baseline's mean. Its best episode (131) exceeds every other agent's maximum.

## Reproducing

```bash
make docker-build
make docker-run ITERATIONS=1000
make docker-evaluate EPISODES=1000
```

Live monitoring during training:

```bash
make monitor-rl
```
