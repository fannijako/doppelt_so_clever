# TODO — Future Development

### Issues & Suggestions

1. **Break up `Renderer` (496 lines)** — `_render_blue_panel`, `_render_green_panel`, and `_render_pink_panel` are nearly identical. Extract a shared `_render_box_row()` helper or per-section `PanelRenderer` classes.
1. **Add tests for new code** — `Board.to_dict()` serialization is highly testable. `Renderer` can be smoke-tested by verifying it doesn't crash given a `RenderSnapshot`.
1. **Visual overflow** on the buttons in case of long texts, e.g. yellow action list or grey question mark
1. **Not all actions received**
1. **Fox number not updated** but given in the action list
1. **Scoring instructions** are not added visually
1. **Placement decisions** are on the board and not with buttons
1. **Dice selection** is on the dice, not with buttons
1. **General overview** of implementation vs rules

## Reinforcement Learning

- [ ] **Create `RLObserver(GameObserver)`** — Capture game events into (state, action, reward) tuples. Use `Board.to_dict()` to build state vectors on `on_board_updated()`. Use `on_game_ended(score)` for the terminal reward.
- [ ] **Create `RLInputHandler(InputHandler)`** — Return actions from a policy network. The existing `choose_index()` / `confirm()` / `choose_value()` interface maps directly to discrete action selection.
- [ ] **Consider a `Game.step()` API** — The current `Game.play()` runs an entire episode. For standard Gymnasium/Gym integration, a `step(action) → (state, reward, done, info)` interface would be more natural. This is a larger refactor; the InputHandler-based approach works for simpler RL setups (e.g. policy gradient over full episodes).
- [ ] **Consider an `on_decision_point` observer event** — Fire before the input handler is called, passing the available options. This lets an RL observer capture (state, action_space) pairs without coupling to the InputHandler.
- [x] **Add `Board.to_tensor()`** — Converts `to_dict()` output into a fixed-size 372-float vector normalised to [0, 1] for neural network input.
