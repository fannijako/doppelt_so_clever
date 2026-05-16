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

- **Normalize reward scale**
  - Keep rewards in a stable range, for example by dividing final score by `300` or using shaped deltas with controlled weights.
  - Prevent value loss from dominating PPO.

- **Tune PPO after structural fixes**
  - Revisit `entropy_coefficient`, `value_loss_coefficient`, `gamma`, `gae_lambda`, and batch size only after reward/action fixes are in place.

- **Use curriculum carefully**
  - Train first on fewer rounds only if shaped rewards are active.
  - Validate that curriculum evaluation always transitions back to full six-round games.

## Phase 5: Evaluation and regression tracking

- **Add stronger baselines**
  - Keep random and always-accept baselines.
  - Add heuristic baselines for greedy immediate score, fox balancing, and resource-aware play.
  - Use these as meaningful thresholds.

- **Track score categories**
  - Log the percentage of games in each official category: `<140`, `140-159`, `160-179`, `180-199`, `200-219`, and higher.

- **Checkpoint best model by evaluation score**
  - Save the best checkpoint using separate evaluation episodes, not only the latest training iteration.
  - Avoid selecting noisy checkpoints from small training batches.

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
