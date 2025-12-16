import pytest

from src.pink_box import PinkBox
from src.actions import Action


def test_pink_box_invalid_input():
    with pytest.raises(ValueError):
        PinkBox(1, Action.NONE)


def test_pink_box_valid_input():
    pink_box = PinkBox(1, Action.REROLL)
    assert pink_box.action_filter_limit == 1
    assert pink_box.action == Action.REROLL
    assert pink_box.value_used is None


def test_pink_box_add_die_value():
    pink_box = PinkBox(0, Action.NONE)
    pink_box.add_die_value(1)
    assert pink_box.value_used == 1


def test_pink_box_str():
    pink_box = PinkBox(1, Action.REROLL)
    assert str(pink_box) == "Pink box: >= 1 | reroll: None"
