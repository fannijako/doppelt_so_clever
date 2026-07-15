from src.board.board import Board
from src.dice.dice_color import DiceColor
from src.ui.theme import load_fonts
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


class TestRenderTargets:
    def test_selectable_die_returned_as_target(self, display_screen, build_die):
        die = build_die(DiceColor.WHITE, 5)
        renderer = Renderer(display_screen, load_fonts())
        targets = renderer.render(_snapshot(Board(), [die], selectable={id(die)}), Layout.compute(1280, 800))
        assert len(targets.dice) == 1

    def test_waiting_prompt_renders_one_button_per_option(self, display_screen, build_die):
        die = build_die(DiceColor.WHITE, 5)
        renderer = Renderer(display_screen, load_fonts())
        targets = renderer.render(_snapshot(Board(), [die], selectable=set()), Layout.compute(1280, 800))
        assert len(targets.buttons) == 1

    def test_game_over_hides_buttons(self, display_screen, build_die):
        die = build_die(DiceColor.WHITE, 5)
        renderer = Renderer(display_screen, load_fonts())
        snapshot = _snapshot(Board(), [die], selectable=set(), waiting=False, game_over=True)
        targets = renderer.render(snapshot, Layout.compute(1280, 800))
        assert not targets.buttons
