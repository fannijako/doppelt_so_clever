# Phase 3 — Retrain + Eval Runbook

Companion to the [remediation design](../docs/superpowers/specs/2026-07-02-rl-plateau-remediation-design.md),
Phase 3. Two from-scratch runs isolate the two fixes; eval gates compare against
the `best.pt` 108.4 baseline recorded in
[`RL_PLATEAU_DIAGNOSIS.md`](./RL_PLATEAU_DIAGNOSIS.md).

## Runs

Both runs: from scratch (778-dim state is incompatible with old checkpoints),
strategic features on by default, ~2.6 s/iter with `--num-workers 6` on an M-class
8-core → 5000 iterations ≈ 3.5–4 h. Do not run both concurrently on one 8-core box.

**Run A — isolates the observation fix (Phase 1).** No shaping + strategic features.

```bash
python main.py train --reward-mode none --num-workers 6 \
  --checkpoint-dir model/checkpoints_runA --log-dir runs/runA
```

Launched 2026-07-02 from a worktree pinned at the Phase 1 tip
(`doppelt_so_clever-runA`, `--no-shaped-rewards` pre-flip syntax; defaults wrote to
the worktree's `model/checkpoints` / `runs/doppelt_rl`).

**Run B — isolates the shaping fix (Phase 2).** Min-section PBRS + strategic features.

```bash
python main.py train --reward-mode min-section --num-workers 6 \
  --checkpoint-dir model/checkpoints_runB --log-dir runs/runB
```

Start after Run A finishes (core contention) and after the Phase 2 PR is merged.

## Monitoring

```bash
make monitor-rl MONITOR_ARGS="--log-dir <log-dir>"        # 10-min polling
make monitor-rl MONITOR_ARGS="--log-dir <log-dir> --once" # snapshot
```

TensorBoard health criteria (from the design):

- `loss/entropy` stays healthy (≳0.2; no collapse toward 1e-10).
- `score/mean` clears ~116 (the old no-shaping ceiling).
- `score/max` *sustained* toward 160+, not spiky single batches.

Abort early if entropy collapses or `score/mean` flatlines below the old curve for
>500 iterations.

## Eval gates (per run, on its `best.pt`)

```bash
python main.py section-report --checkpoint <ckpt-dir>/best.pt -n 300
python main.py evaluate -n 300 --checkpoint <ckpt-dir>/best.pt --ci
```

Compare the section report against the baseline block in
`RL_PLATEAU_DIAGNOSIS.md` (§ Evidence):

| Metric | Baseline (`best.pt` @108.4) | Success |
|---|---|---|
| total mean | 108.4 | materially above 116 |
| blue mean | 5.9 | materially up |
| yellow mean | 3.3 | materially up |
| %≥140 | 3.0% | materially above 3.0% |
| %≥160 | 0.0% | > 0 |
| foxes/game | 0.6 | above baseline (fox pathway live) |
| `evaluate --ci` | exit 0 | exit 0 |

Paste each run's section report into
[`RL_TRAINING_JOURNEY.md`](./RL_TRAINING_JOURNEY.md) as the regenerated
per-section evidence.

## Decision

- Run A ≥ gates, Run B < Run A → ship Run A's checkpoint; keep `none` as default.
- Run B ≥ gates and ≥ Run A → flip the training default to `min-section`
  (scope decision 2's deferred flip) and ship Run B's checkpoint.
- Both stall below gates → Phase 4 (capacity: bigger trunk, attention over the
  option block, curriculum, PBT) — conditional, not speculative.

Shipping a checkpoint = copy to `model/checkpoints/best.pt` so `play --mode model`
/ `--mode interactive` pick it up (the parity contract will refuse a stale
observer config automatically).
