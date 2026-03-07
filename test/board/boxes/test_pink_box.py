import pytest

from src.board.boxes.pink_box import PinkBox
from src.actions.action_type import ActionType


def test_pink_box_invalid_input():
    with pytest.raises(ValueError):
        PinkBox(1, ActionType.NONE)


def test_pink_box_valid_input():
    pink_box = PinkBox(1, ActionType.REROLL)
    assert pink_box.action_filter_limit == 1
    assert pink_box.action == ActionType.REROLL
    assert pink_box.value_used is None


def test_pink_box_add_dice_value():
    pink_box = PinkBox(0, ActionType.NONE)
    pink_box.add_dice_value(1)
    assert pink_box.value_used == 1


def test_pink_box_str():
    pink_box = PinkBox(1, ActionType.REROLL)
    assert str(pink_box) == "Pink box: >= 1 | reroll: None"
