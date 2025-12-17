import pytest

from src.blue_box import BlueBox
from src.actions import Action


def test_blue_box_invalid_input():
    with pytest.raises(ValueError):
        BlueBox(0, Action.NONE)

    with pytest.raises(ValueError):
        BlueBox(13, Action.NONE)


def test_blue_box_valid_input():
    blue_box = BlueBox(1, Action.REROLL)
    assert blue_box.maximum_value_limit == 1
    assert blue_box.action == Action.REROLL
    assert blue_box.value_used is None


def test_blue_box_add_dice_value():
    blue_box = BlueBox(12, Action.NONE)
    blue_box.add_dice_value(1, 1)
    assert blue_box.value_used == 2


def test_blue_box_str():
    blue_box = BlueBox(1, Action.REROLL)
    assert str(blue_box) == "blue box: 1 >= | reroll: None"
