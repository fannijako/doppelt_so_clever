# TODO — Future Development

### Issues & Suggestions

- [ ] **Break up `Renderer` (496 lines)** — `_render_blue_panel`, `_render_green_panel`, and `_render_pink_panel` are nearly identical. Extract a shared `_render_box_row()` helper or per-section `PanelRenderer` classes.
- [ ] **Pass `PygameUI` explicitly instead of `_find_pygame_ui`** — `_find_pygame_ui()` walks the observer tree and returns `None` for non-interactive modes. If the composite is wrapped differently it silently breaks. Pass the UI reference directly.
- [ ] **Fix fragile `id()` dice comparison** — `Renderer._render_dice_section` mixes `__eq__`-based `in` with `id()` identity checks. If `Dice` objects are ever copied this breaks. Rely on a single consistent comparison.
- [ ] **Handle quit during `wait_for_input`** — If the user quits while the game thread is blocked, `_input_result` stays `None` and is returned as `int`, crashing downstream. Return a sentinel or raise an exception.
- [ ] **Add tests for new code** — `Board.to_dict()` serialization is highly testable. `Renderer` can be smoke-tested by verifying it doesn't crash given a `RenderSnapshot`.

## Reinforcement Learning

- [ ] **Create `RLObserver(GameObserver)`** — Capture game events into (state, action, reward) tuples. Use `Board.to_dict()` to build state vectors on `on_board_updated()`. Use `on_game_ended(score)` for the terminal reward.
- [ ] **Create `RLInputHandler(InputHandler)`** — Return actions from a policy network. The existing `choose_index()` / `confirm()` / `choose_value()` interface maps directly to discrete action selection.
- [ ] **Consider a `Game.step()` API** — The current `Game.play()` runs an entire episode. For standard Gymnasium/Gym integration, a `step(action) → (state, reward, done, info)` interface would be more natural. This is a larger refactor; the InputHandler-based approach works for simpler RL setups (e.g. policy gradient over full episodes).
- [ ] **Consider an `on_decision_point` observer event** — Fire before the input handler is called, passing the available options. This lets an RL observer capture (state, action_space) pairs without coupling to the InputHandler.
- [ ] **Add `Board.to_tensor()`** — Once the RL framework is chosen (PyTorch / JAX / etc.), add a method that converts `to_dict()` output into a fixed-size numeric tensor suitable for neural network input.
