# RL Training Fix Plan

## Goal

Improve the reinforcement learning agent for Doppelt so clever by addressing the structural causes of the current score ceiling below `160` points.

## Phase 1: Fix environment correctness

- **Status: complete**

- **Fix immediate-action removal**
  - Update `ActionHandler.execute()` so it removes the selected action, not always the first action.
  - Add tests for selecting action index `0`, a middle index, and the last index.
  - Expected result: chained immediate actions execute according to the user/model's actual choice.

- **Audit failed/no-op placements**
  - Identify where invalid placement choices are silently converted to empty action lists.
  - Make these outcomes detectable by the RL reward layer.
  - Expected result: the agent can be penalized for choices that waste dice/actions.

## Phase 2: Add useful reward signals

- **Introduce per-transition rewards**
  - Extend RL transitions or trajectory conversion to support step rewards.
  - Keep final score as a terminal reward, but add intermediate rewards after meaningful events.

- **Reward board progress**
  - On board updates, compare board state before and after the decision.
  - Reward score delta estimates, newly filled/crossed boxes, resource gains, and fox gains.
  - Penalize failed placements, skipped placement when legal progress was possible, and resource use without board improvement.

- **Update GAE**
  - Change `compute_gae()` from terminal-only reward to per-step reward accumulation.
  - Preserve a terminal score bonus.
  - Update tests currently asserting terminal-only behavior.

- **Validation**
  - Unit tests prove rewards appear on intermediate transitions.
  - A random policy's reward distribution should be non-zero before terminal state.

## Phase 3: Fix observation/action aliasing

- **Status: complete**

- **Enable prompt augmentation by default**
  - Set augmented observations as the default for training.
  - Ensure evaluation, Monte Carlo, UI advisor, and checkpoint loading use matching state size.
  - Store `state_size` and `augmented` metadata in checkpoints.

- **Encode option semantics**
  - Add structured option features instead of only `num_options`.
  - Start with the highest-impact prompts: die color/value choices, placement choices, immediate action choices, and confirm prompts.
  - Include these features in the policy input or use separate heads per decision family.

- **Avoid raw index learning**
  - Prefer action representations such as choosing a die color, placement coordinate, action type, or yes/no with prompt type.
  - Map semantic actions to legal options at runtime.

- **Validation**
  - Tests verify two prompts with the same option count produce different state features.
  - Tests verify options with different semantic content produce different encodings.

## Phase 4: Improve training setup

- **Status: complete**

- **Normalize reward scale**
  - Terminal score is scaled by `DEFAULT_TERMINAL_REWARD_SCALE = 1/300` in `model/rl_utils.py`, applied at the `convert_trajectory` boundary.
  - `--terminal-reward-scale` CLI knob on both `train` and `pbt-train`.

- **Tune PPO after structural fixes**
  - `PPOConfig` now carries `gamma` and `gae_lambda`; threaded through `build_batch` → `compute_gae`.
  - New CLI knobs on both training scripts: `--gamma`, `--gae-lambda`, `--minibatch-size`.

- **Use curriculum carefully**
  - `--curriculum` requires shaped rewards on; combining it with `--no-shaped-rewards` raises at config build time.
  - When curriculum is active, early-stop scoring runs a separate full-6-round eval (`--curriculum-eval-episodes`, default 16) instead of trusting truncated training scores.

## Phase 5: Evaluation and regression tracking

- **Status: complete**

- **Add stronger baselines**
  - Random and always-accept baselines retained.
  - Three rule-based heuristic baselines added in `src/input_handler/heuristics/`: `GreedyImmediateInputHandler`, `FoxBalancingInputHandler`, `ResourceAwareInputHandler`.
  - All five baselines registered in `scripts/evaluate_rl.py:_BASELINES`.

- **Track score categories**
  - `_category_distribution()` + `_print_category_table()` in `scripts/evaluate_rl.py` print percentages per agent in each official band: `<140`, `140-159`, `160-179`, ..., `>=320`.
  - Grouped bar chart saved as `score_categories.png` alongside the existing overlay histogram.

- **Checkpoint best model by evaluation score**
  - `EvalConfig` (`interval`, `episodes`) and `_maybe_eval_and_save_best()` run full-6-round eval and overwrite `model/checkpoints/best.pt` whenever a new best mean score is reached.
  - `--eval-interval` (default 50) and `--eval-episodes` (default 32) CLI flags on `train`.
  - Best checkpoints store `best_eval_score` and `best_eval_iteration` on top of the standard Phase 3 metadata payload.
  - `scripts/evaluate_rl.py:_find_latest_checkpoint()` prefers `best.pt` over the latest numeric checkpoint.

- **Acceptance targets**
  - Short term: consistently exceed always-accept.
  - Medium term: mean score above `180`.
  - Long term: mean score above `200`, with non-trivial games above `240`.

## Recommended implementation order

1. Fix `ActionHandler` selected-action removal.
2. Add per-step rewards and GAE support.
3. Enable and store augmented observations consistently.
4. Add semantic option encoding.
5. Retrain and compare against stronger baselines.

## Summary

The plan is to first make the environment reliable, then give PPO denser feedback, then remove action/state ambiguity. These three fixes address the core failure modes most likely responsible for the score ceiling below `160`.
