import pytest

from src.blue_board_part import BlueBoardPart
from src.die import Die, DieColor
from src.actions import Action


def test_add_die_return_action_on_first_box(blue_and_white_dies):
    blue_board_part = BlueBoardPart()
    blue_die, white_die = blue_and_white_dies
    assert blue_board_part.add_die(blue_die, white_die) == Action.NONE


def test_add_die_return_action_on_second_box(blue_and_white_dies):
    blue_board_part = BlueBoardPart()
    blue_die, white_die = blue_and_white_dies
    blue_board_part.add_die(blue_die, white_die)
    assert blue_board_part.add_die(blue_die, white_die) == Action.REUSE


def test_add_die_return_action_on_third_box(blue_and_white_dies):
    blue_board_part = BlueBoardPart()
    blue_die, white_die = blue_and_white_dies
    blue_board_part.add_die(blue_die, white_die)
    blue_board_part.add_die(blue_die, white_die)
    assert blue_board_part.add_die(blue_die, white_die) == Action.YELLOW_QUESTION_MARK


def test_fail_on_add_die_with_different_color():
    with pytest.raises(ValueError):
        blue_board_part = BlueBoardPart()
        blue_die = Die(DieColor.GREEN)
        blue_die.roll()
        white_die = Die(DieColor.WHITE)
        white_die.roll()
        blue_board_part.add_die(blue_die, white_die)


def test_fail_on_add_die_with_unrolled_die():
    with pytest.raises(ValueError):
        blue_board_part = BlueBoardPart()
        blue_die = Die(DieColor.BLUE)
        white_die = Die(DieColor.WHITE)
        blue_board_part.add_die(blue_die, white_die)


def test_fail_on_add_die_with_full_board(blue_and_white_dies):
    blue_board_part = BlueBoardPart()
    blue_die, white_die = blue_and_white_dies
    for _ in range(12):
        blue_board_part.add_die(blue_die, white_die)

    with pytest.raises(ValueError):
        blue_board_part.add_die(blue_die, white_die)


def test_evaluate(blue_and_white_dies):
    blue_board_part = BlueBoardPart()
    blue_die, white_die = blue_and_white_dies
    assert blue_board_part.evaluate() == 0

    blue_board_part.add_die(blue_die, white_die)
    assert blue_board_part.evaluate() == 1

    blue_board_part.add_die(blue_die, white_die)
    assert blue_board_part.evaluate() == 3
