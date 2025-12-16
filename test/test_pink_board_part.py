import pytest

from src.pink_board_part import PinkBoardPart
from src.die import Die, DieColor
from src.actions import Action


def test_add_die_return_action_on_first_box():
    pink_board_part = PinkBoardPart()
    die = Die(DieColor.PINK)
    die.roll()
    assert pink_board_part.add_die(die) == Action.NONE


def test_add_die_return_action_on_second_box():
    pink_board_part = PinkBoardPart()

    die = Die(DieColor.PINK)
    die.roll()
    pink_board_part.add_die(die)

    die2 = Die(DieColor.PINK)
    die2.roll()
    assert pink_board_part.add_die(die2) == Action.NONE


def test_add_die_return_action_on_third_box():
    pink_board_part = PinkBoardPart()

    die = Die(DieColor.PINK)
    die.roll()
    pink_board_part.add_die(die)

    die2 = Die(DieColor.PINK)
    die2.roll()
    pink_board_part.add_die(die2)

    die3 = Die(DieColor.PINK)
    die3.value = 2
    assert pink_board_part.add_die(die3) == Action.REROLL


def test_add_die_return_none_action_on_third_box():
    pink_board_part = PinkBoardPart()

    die = Die(DieColor.PINK)
    die.roll()
    pink_board_part.add_die(die)

    die2 = Die(DieColor.PINK)
    die2.roll()
    pink_board_part.add_die(die2)

    die3 = Die(DieColor.PINK)
    die3.value = 1
    assert pink_board_part.add_die(die3) == Action.NONE


def test_fail_on_add_die_with_different_color():
    with pytest.raises(ValueError):
        pink_board_part = PinkBoardPart()
        die = Die(DieColor.GREEN)
        die.roll()
        pink_board_part.add_die(die)


def test_not_fail_on_add_die_with_white():
    pink_board_part = PinkBoardPart()
    die = Die(DieColor.WHITE)
    die.roll()
    pink_board_part.add_die(die)


def test_fail_on_add_die_with_unrolled_die():
    with pytest.raises(ValueError):
        pink_board_part = PinkBoardPart()
        die = Die(DieColor.PINK)
        pink_board_part.add_die(die)


def test_fail_on_add_die_with_full_board():
    pink_board_part = PinkBoardPart()
    die = Die(DieColor.PINK)
    die.roll()
    for _ in range(12):
        pink_board_part.add_die(die)

    with pytest.raises(ValueError):
        pink_board_part.add_die(die)


def test_evaluate():
    pink_board_part = PinkBoardPart()
    die = Die(DieColor.WHITE)
    die.value = 2
    pink_board_part.add_die(die)
    assert pink_board_part.evaluate() == 2

    die2 = Die(DieColor.PINK)
    die2.value = 3
    pink_board_part.add_die(die2)
    assert pink_board_part.evaluate() == 5
