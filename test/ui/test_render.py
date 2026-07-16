from src.board.board import Board
from src.dice.dice_color import DiceColor
from src.ui.theme import load_ui_font, font_name_or_fallback
from src.ui.layout import Layout
from src.ui.renderer import Renderer
from src.ui.render_snapshot import RenderSnapshot


def _snapshot(board, dice, *, selectable, waiting=True, game_over=False):
    return RenderSnapshot(
        board_data=board.to_dict(), dice=dice, available_dice=dice, picked_dice=[], discarded_dice=[],
        round_number=1, is_active_round=True, subround=1, prompt="Pick", options=["white"],
        is_waiting=waiting, score=0, is_game_over=game_over, won_actions=[], popup_notifications=[],
        selectable_die_ids=selectable,
    )


def _render(window, snapshot):
    window.clear()
    return Renderer(font_name_or_fallback(load_ui_font())).render(snapshot, Layout.compute(1280, 800))


class TestRenderSmoke:
    def test_dice_returned_as_targets(self, arcade_window, build_die):
        die = build_die(DiceColor.WHITE, 5)
        targets = _render(arcade_window, _snapshot(Board(), [die], selectable={id(die)}))
        assert any(target is die for target, _ in targets.dice)

    def test_waiting_prompt_renders_one_button_per_option(self, arcade_window, build_die):
        die = build_die(DiceColor.WHITE, 5)
        targets = _render(arcade_window, _snapshot(Board(), [die], selectable=set()))
        assert len(targets.buttons) == 1

    def test_game_over_hides_buttons(self, arcade_window, build_die):
        die = build_die(DiceColor.WHITE, 5)
        snapshot = _snapshot(Board(), [die], selectable=set(), waiting=False, game_over=True)
        targets = _render(arcade_window, snapshot)
        assert not targets.buttons
