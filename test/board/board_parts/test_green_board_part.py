import pytest

from src.board.board_parts.green_board_part import GreenBoardPart
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.actions.action_type import ActionType


def test_add_dice_return_action_on_first_box():
    green_board_part = GreenBoardPart()
    dice = Dice(DiceColor.GREEN)
    dice.roll()
    assert green_board_part.add_dice(dice) == ActionType.NONE


def test_add_dice_return_action_on_second_box():
    green_board_part = GreenBoardPart()

    dice = Dice(DiceColor.GREEN)
    dice.roll()
    green_board_part.add_dice(dice)

    dice2 = Dice(DiceColor.GREEN)
    dice2.roll()
    assert green_board_part.add_dice(dice2) == ActionType.REROLL


def test_add_dice_return_action_on_third_box():
    green_board_part = GreenBoardPart()

    dice = Dice(DiceColor.GREEN)
    dice.roll()
    green_board_part.add_dice(dice)

    dice2 = Dice(DiceColor.GREEN)
    dice2.roll()
    green_board_part.add_dice(dice2)

    dice3 = Dice(DiceColor.GREEN)
    dice3.value = 2
    assert green_board_part.add_dice(dice3) == ActionType.NONE


def test_fail_on_add_dice_with_different_color():
    with pytest.raises(ValueError):
        green_board_part = GreenBoardPart()
        dice = Dice(DiceColor.PINK)
        dice.roll()
        green_board_part.add_dice(dice)


def test_not_fail_on_add_dice_with_white():
    green_board_part = GreenBoardPart()
    dice = Dice(DiceColor.WHITE)
    dice.roll()
    green_board_part.add_dice(dice)


def test_fail_on_add_dice_with_unrolled_dice():
    with pytest.raises(ValueError):
        green_board_part = GreenBoardPart()
        dice = Dice(DiceColor.GREEN)
        green_board_part.add_dice(dice)


def test_fail_on_add_dice_with_full_board():
    green_board_part = GreenBoardPart()
    dice = Dice(DiceColor.GREEN)
    dice.roll()
    for _ in range(12):
        green_board_part.add_dice(dice)

    with pytest.raises(IndexError):
        green_board_part.add_dice(dice)


def test_evaluate():
    green_board_part = GreenBoardPart()
    dice = Dice(DiceColor.WHITE)
    dice.value = 3
    green_board_part.add_dice(dice)
    assert green_board_part.evaluate() == 0

    dice2 = Dice(DiceColor.GREEN)
    dice2.value = 2
    green_board_part.add_dice(dice2)
    assert green_board_part.evaluate() == 2
