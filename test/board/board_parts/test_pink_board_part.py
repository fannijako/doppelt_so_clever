import pytest

from src.board.board_parts.pink_board_part import PinkBoardPart
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.actions.action_type import ActionType
from src.actions.action_map import ActionMap


def test_add_dice_return_action_on_first_box():
    pink_board_part = PinkBoardPart()
    dice = Dice(DiceColor.PINK)
    dice.roll()
    assert pink_board_part.add_dice(dice) == ActionMap.get(ActionType.NONE)


def test_add_dice_return_action_on_second_box():
    pink_board_part = PinkBoardPart()

    dice = Dice(DiceColor.PINK)
    dice.roll()
    pink_board_part.add_dice(dice)

    dice2 = Dice(DiceColor.PINK)
    dice2.roll()
    assert pink_board_part.add_dice(dice2) == ActionMap.get(ActionType.NONE)


def test_add_dice_return_action_on_third_box():
    pink_board_part = PinkBoardPart()

    dice = Dice(DiceColor.PINK)
    dice.roll()
    pink_board_part.add_dice(dice)

    dice2 = Dice(DiceColor.PINK)
    dice2.roll()
    pink_board_part.add_dice(dice2)

    dice3 = Dice(DiceColor.PINK)
    dice3.value = 2
    assert pink_board_part.add_dice(dice3) == ActionMap.get(ActionType.REROLL)


def test_add_dice_return_none_action_on_third_box():
    pink_board_part = PinkBoardPart()

    dice = Dice(DiceColor.PINK)
    dice.roll()
    pink_board_part.add_dice(dice)

    dice2 = Dice(DiceColor.PINK)
    dice2.roll()
    pink_board_part.add_dice(dice2)

    dice3 = Dice(DiceColor.PINK)
    dice3.value = 1
    assert pink_board_part.add_dice(dice3) == ActionMap.get(ActionType.NONE)


def test_fail_on_add_dice_with_different_color():
    with pytest.raises(ValueError):
        pink_board_part = PinkBoardPart()
        dice = Dice(DiceColor.GREEN)
        dice.roll()
        pink_board_part.add_dice(dice)


def test_not_fail_on_add_dice_with_white():
    pink_board_part = PinkBoardPart()
    dice = Dice(DiceColor.WHITE)
    dice.roll()
    pink_board_part.add_dice(dice)


def test_fail_on_add_dice_with_unrolled_dice():
    with pytest.raises(ValueError):
        pink_board_part = PinkBoardPart()
        dice = Dice(DiceColor.PINK)
        pink_board_part.add_dice(dice)


def test_fail_on_add_dice_with_full_board():
    pink_board_part = PinkBoardPart()
    dice = Dice(DiceColor.PINK)
    dice.roll()
    for _ in range(12):
        pink_board_part.add_dice(dice)

    with pytest.raises(ValueError):
        pink_board_part.add_dice(dice)


def test_evaluate():
    pink_board_part = PinkBoardPart()
    dice = Dice(DiceColor.WHITE)
    dice.value = 2
    pink_board_part.add_dice(dice)
    assert pink_board_part.evaluate() == 2

    dice2 = Dice(DiceColor.PINK)
    dice2.value = 3
    pink_board_part.add_dice(dice2)
    assert pink_board_part.evaluate() == 5
