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
