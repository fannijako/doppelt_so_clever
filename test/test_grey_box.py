import pytest

from src.board.boxes.grey_box import GreyBox
from src.dice import DiceColor


def test_grey_box_invalid_input():
    with pytest.raises(ValueError):
        GreyBox(DiceColor.GREEN, 0)


def test_grey_box_valid_input():
    grey_box = GreyBox(DiceColor.GREEN, 1)
    assert grey_box.number == 1
    assert grey_box.color == DiceColor.GREEN
    assert grey_box.is_crossed is False


def test_grey_box_cross_box():
    grey_box = GreyBox(DiceColor.GREEN, 1)
    grey_box.cross_box(DiceColor.GREEN, 1)
    assert grey_box.is_crossed is True


def test_grey_box_cross_box_invalid_input():
    grey_box = GreyBox(DiceColor.GREEN, 1)
    grey_box.cross_box(DiceColor.GREEN, 2)
    assert grey_box.is_crossed is False


def test_grey_box_str():
    grey_box = GreyBox(DiceColor.GREEN, 1)
    assert str(grey_box) == "Grey box: green | 1 | crossed: False"
