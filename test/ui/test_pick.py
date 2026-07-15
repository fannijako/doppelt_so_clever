from src.ui.pick import build_pick_map
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
