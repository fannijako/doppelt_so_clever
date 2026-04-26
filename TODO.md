# TODO — Future Development

## UI (Pygame Interactive Mode)

- [ ] **Create a display surface and render loop** — `PygameUI._render()` currently only calls `pygame.event.pump()`. Build actual drawing logic for the board, dice, and prompts.
- [ ] **Handle Pygame events** — Process `QUIT`, `MOUSEBUTTONDOWN`, `KEYDOWN`, etc. so the user can interact with the window.
- [ ] **Wire clicks to `submit_input()`** — `PygameUI.wait_for_input()` blocks until `submit_input()` is called, but nothing calls it yet. Map UI clicks/keypresses to option indices and call `submit_input(index)`.
- [ ] **Run game logic on a background thread** — Pygame's event loop must run on the main thread (especially on macOS). Move `Game.play()` to a background thread and keep the Pygame loop on main.
- [ ] **Add thread safety to `PygameUI`** — `current_dice`, `available_dice`, and `board` are mutated from the game thread and will be read from the render thread. Guard shared state with a lock.
- [ ] **Use `Board.to_dict()` for rendering** — Read board state through the structured snapshot rather than reaching into board part internals.

## Reinforcement Learning

- [ ] **Create `RLObserver(GameObserver)`** — Capture game events into (state, action, reward) tuples. Use `Board.to_dict()` to build state vectors on `on_board_updated()`. Use `on_game_ended(score)` for the terminal reward.
- [ ] **Create `RLInputHandler(InputHandler)`** — Return actions from a policy network. The existing `choose_index()` / `confirm()` / `choose_value()` interface maps directly to discrete action selection.
- [ ] **Consider a `Game.step()` API** — The current `Game.play()` runs an entire episode. For standard Gymnasium/Gym integration, a `step(action) → (state, reward, done, info)` interface would be more natural. This is a larger refactor; the InputHandler-based approach works for simpler RL setups (e.g. policy gradient over full episodes).
- [ ] **Consider an `on_decision_point` observer event** — Fire before the input handler is called, passing the available options. This lets an RL observer capture (state, action_space) pairs without coupling to the InputHandler.
- [ ] **Add `Board.to_tensor()`** — Once the RL framework is chosen (PyTorch / JAX / etc.), add a method that converts `to_dict()` output into a fixed-size numeric tensor suitable for neural network input.
