import pytest

from src.green_box import GreenBox
from src.actions.actions import ActionType


def test_green_box_invalid_input():
    with pytest.raises(ValueError):
        GreenBox(0, ActionType.NONE, 0)


def test_green_box_valid_input():
    green_box = GreenBox(1, ActionType.REROLL, 0)
    assert green_box.value_multiplier == 1
    assert green_box.action == ActionType.REROLL
    assert green_box.value_used is None


def test_green_box_add_dice_value():
    green_box = GreenBox(2, ActionType.NONE, 0)
    green_box.add_dice_value(1)
    assert green_box.value_used == 2


def test_green_box_str():
    green_box = GreenBox(1, ActionType.REROLL, 0)
    assert str(green_box) == "Green box: 1x | reroll: None"
