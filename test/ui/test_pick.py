from src.ui.geometry import Rect
from src.ui.pick import build_pick_map, die_index_at, button_index_at
from src.dice.dice_color import DiceColor


class TestBuildPickMap:
    def test_die_option_maps_by_identity(self, build_die):
        first = build_die(DiceColor.WHITE, 5)
        second = build_die(DiceColor.BLUE, 3)
        pick_map = build_pick_map([first, second], [first, second])
        assert pick_map[id(second)] == 1

    def test_color_option_maps_to_matching_die(self, build_die):
        white = build_die(DiceColor.WHITE, 5)
        green = build_die(DiceColor.GREEN, 6)
        pick_map = build_pick_map(["white", "green"], [white, green])
        assert pick_map[id(green)] == 1

    def test_confirm_options_map_nothing(self, build_die):
        die = build_die(DiceColor.WHITE, 5)
        assert not build_pick_map(["yes", "no"], [die])


class TestDieIndexAt:
    def test_hit_selectable_die_returns_pick_value(self, build_die):
        die = build_die(DiceColor.WHITE, 5)
        assert die_index_at([(die, Rect(0, 0, 50, 50))], {id(die): 3}, (10, 10)) == 3

    def test_die_absent_from_pick_map_is_ignored(self, build_die):
        die = build_die(DiceColor.WHITE, 5)
        assert die_index_at([(die, Rect(0, 0, 50, 50))], {}, (10, 10)) is None

    def test_click_outside_rect_is_ignored(self, build_die):
        die = build_die(DiceColor.WHITE, 5)
        assert die_index_at([(die, Rect(0, 0, 50, 50))], {id(die): 3}, (80, 80)) is None


class TestButtonIndexAt:
    def test_returns_index_of_hit_button(self):
        rects = [Rect(0, 0, 40, 40), Rect(60, 0, 40, 40)]
        assert button_index_at(rects, (70, 10)) == 1

    def test_returns_none_when_no_button_hit(self):
        assert button_index_at([Rect(0, 0, 40, 40)], (100, 100)) is None
