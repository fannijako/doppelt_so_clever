import pytest

from src.green_board_part import GreenBoardPart
from src.die import Die, DieColor
from src.actions import Action


def test_add_die_return_action_on_first_box():
    green_board_part = GreenBoardPart()
    die = Die(DieColor.GREEN)
    die.roll()
    assert green_board_part.add_die(die) == Action.NONE


def test_add_die_return_action_on_second_box():
    green_board_part = GreenBoardPart()

    die = Die(DieColor.GREEN)
    die.roll()
    green_board_part.add_die(die)

    die2 = Die(DieColor.GREEN)
    die2.roll()
    assert green_board_part.add_die(die2) == Action.REROLL


def test_add_die_return_action_on_third_box():
    green_board_part = GreenBoardPart()

    die = Die(DieColor.GREEN)
    die.roll()
    green_board_part.add_die(die)

    die2 = Die(DieColor.GREEN)
    die2.roll()
    green_board_part.add_die(die2)

    die3 = Die(DieColor.GREEN)
    die3.value = 2
    assert green_board_part.add_die(die3) == Action.NONE


def test_fail_on_add_die_with_different_color():
    with pytest.raises(ValueError):
        green_board_part = GreenBoardPart()
        die = Die(DieColor.PINK)
        die.roll()
        green_board_part.add_die(die)


def test_not_fail_on_add_die_with_white():
    green_board_part = GreenBoardPart()
    die = Die(DieColor.WHITE)
    die.roll()
    green_board_part.add_die(die)


def test_fail_on_add_die_with_unrolled_die():
    with pytest.raises(ValueError):
        green_board_part = GreenBoardPart()
        die = Die(DieColor.GREEN)
        green_board_part.add_die(die)


def test_fail_on_add_die_with_full_board():
    green_board_part = GreenBoardPart()
    die = Die(DieColor.GREEN)
    die.roll()
    for _ in range(12):
        green_board_part.add_die(die)

    with pytest.raises(ValueError):
        green_board_part.add_die(die)


def test_evaluate():
    green_board_part = GreenBoardPart()
    die = Die(DieColor.WHITE)
    die.value = 3
    green_board_part.add_die(die)
    assert green_board_part.evaluate() == 0

    die2 = Die(DieColor.GREEN)
    die2.value = 2
    green_board_part.add_die(die2)
    assert green_board_part.evaluate() == 2
