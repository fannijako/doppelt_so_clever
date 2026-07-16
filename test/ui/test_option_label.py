from src.dice.dice_color import DiceColor
from src.board.board_parts.yellow_board_part import YellowBoardAction
from src.ui.widgets import Painter
from src.ui.theme import load_ui_font, font_name_or_fallback
from src.ui.renderer import option_label, fit_size


def _painter(window) -> Painter:
    return Painter(window.height, 1.0, font_name_or_fallback(load_ui_font()))


class TestOptionLabel:
    def test_string_option_is_title_cased(self):
        assert option_label("yellow") == "Yellow"

    def test_die_option_shows_color_and_value(self, build_die):
        assert option_label(build_die(DiceColor.WHITE, 5)) == "White  5"

    def test_placement_tuple_shows_one_indexed_cell(self):
        assert option_label((0, 1, YellowBoardAction.CROSS)) == "R1·C2"

    def test_question_mark_placement_prefixes_value(self):
        assert option_label((3, 0, 1, YellowBoardAction.CROSS)) == "3→R1·C2"

    def test_circle_placement_is_marked(self):
        assert option_label((0, 1, YellowBoardAction.CIRCLE)).endswith("○")

    def test_grey_combination_reads_color_and_number(self):
        assert option_label((DiceColor.BLUE, 3)) == "Blue  3"


class TestFitSize:
    def test_long_label_shrinks_below_base(self, arcade_window):
        assert fit_size(_painter(arcade_window), "X" * 40, 100) < 17

    def test_short_label_keeps_base_size(self, arcade_window):
        assert fit_size(_painter(arcade_window), "3", 300) == 17
