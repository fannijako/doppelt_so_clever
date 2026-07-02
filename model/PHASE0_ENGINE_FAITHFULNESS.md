# Phase 0 — Engine Faithfulness Gate

Companion to [`RL_PLATEAU_DIAGNOSIS.md`](./RL_PLATEAU_DIAGNOSIS.md) and the
[remediation design](../docs/superpowers/specs/2026-07-02-rl-plateau-remediation-design.md).
This is the hard gate that must pass before any retrain.

## Verdict: no engine bug. Gate passes.

All five sections score faithfully to [`RULES.md`](../RULES.md), the fox multiplier
matches the rulebook, and fox actions are reachable. **No engine fix and no
re-baseline are required** — the reward landscape is unchanged, so the existing
108–116 baseline evidence in `RL_PLATEAU_DIAGNOSIS.md` remains valid.

The diagnosis doc's three engine-level suspicions do not hold; they are corrected
in the cross-cutting doc-drift PR.

## Per-section scoring vs rulebook

Encoded as one parametrized test per section in
[`test/board/test_scoring_faithfulness.py`](../test/board/test_scoring_faithfulness.py).

| Section | Implementation | Rulebook (`RULES.md`) | Verdict |
|---|---|---|---|
| blue | filled-box count → triangular `{1:1, 2:3, …, 12:78}` | "white number in the star above the last filled-in box" (§ Blue Dice) | faithful |
| green | `die × box multiplier`; per pair `first − second`; trailing odd box dropped | "multiply … subtract the second space from the first … zero if the second space is empty" (§ Green Dice) | faithful |
| pink | Σ recorded die values | "sum of all recorded numbers from the pink row" (§ Pink Dice) | faithful |
| yellow | crossed-box count → `{1:3, …, 10:165}`; circles excluded | "points based on the number of marks … circled do not count" (§ Yellow Dice) | faithful |
| grey | 4 rows, each `marks → {1:2, …, 4:11, …, 6:22}`, summed | "for 4 marks in a line … 11 points … sum of all four rows" (§ Silver Dice) | faithful |

## Fox economy

- **Formula.** `board._score_from_parts()` = `Σ(sections) + foxes × min(sections)`,
  matching "each Fox scores as many points as the player's lowest-scoring area"
  and "if a player scores 0 points in an area, Foxes are worthless" (§ Foxes).
  Both are pinned by tests.
- **Reachability.** `FOX` sits on green box index 6, yellow column 3, and grey
  column 3 — all fillable positions. Pinned by
  `test_fox_action_sits_on_a_reachable_green_box` /
  `test_fox_action_reachable_in_yellow_and_grey_columns`. The `best.pt` agent
  already earns **0.6 foxes/game** (diagnosis evidence), empirically confirming
  fox > 0 is achievable.
- **Why foxes look "dead".** Not an engine ceiling: `foxes × min(section)` is a
  live lever, but shallow breadth-farming keeps `min(section) ≈ 3`, so each fox
  multiplies almost nothing. This is a policy problem addressed by Phase 1
  (observe the min-section) and Phase 2 (reward the min-section), not an engine fix.

## Why no re-baseline

The design gates a re-baseline on *finding and fixing a bug* (the reward
landscape would change). No bug was found, so the four heuristic baselines and the
per-section evidence in `RL_PLATEAU_DIAGNOSIS.md` are unchanged and are not
regenerated. Reachability is demonstrated deterministically by the structural
tests above rather than by a redundant stochastic re-run.
