# pylint: disable=protected-access
import pytest

from src.grey_board_part import GreyBoardPart
from src.dice import DiceColor, Dice
from src.actions.action_type import ActionType


def test_board_init_available_actions():
    grey_board_part = GreyBoardPart()
    assert len(grey_board_part._available_columns_for_action) == 6


def test_board_init_boxes():
    grey_board_part = GreyBoardPart()
    assert len(grey_board_part.boxes) == 24


def test_add_dice_does_not_return_action():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.GREY)
    smaller_die = [Dice(DiceColor.GREEN)]
    dice.value = 5
    smaller_die[0].value = 2
    assert not grey_board_part.add_dice(dice, smaller_die, color_to_use_grey_as=DiceColor.YELLOW)


def test_failure_if_substitute_color_is_not_available():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.GREY)
    smaller_die = [Dice(DiceColor.GREEN)]
    dice.roll()
    smaller_die[0].roll()
    with pytest.raises(ValueError):
        grey_board_part.add_dice(dice, smaller_die)


def test_add_dice_fails_if_dice_has_color_green():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.GREEN)
    dice.value = 4
    with pytest.raises(ValueError):
        grey_board_part.add_dice(dice, [])


def test_add_dice_fails_if_dice_is_not_rolled():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.GREY)
    with pytest.raises(ValueError):
        grey_board_part.add_dice(dice, [], color_to_use_grey_as=DiceColor.YELLOW)


def test_add_dice_fails_if_smaller_die_has_greater_value_than_dice():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.GREY)
    dice.value = 2
    smaller = Dice(DiceColor.YELLOW)
    smaller.value = 5
    with pytest.raises(ValueError):
        grey_board_part.add_dice(dice, [smaller], color_to_use_grey_as=DiceColor.YELLOW)


def test_add_dice_fails_if_smaller_die_has_same_color_as_dice():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.GREY)
    dice.value = 5
    smaller = Dice(DiceColor.GREY)
    smaller.value = 2
    with pytest.raises(ValueError):
        grey_board_part.add_dice(dice, [smaller], color_to_use_grey_as=DiceColor.YELLOW)


def test_add_dice_adds_grey_dice_as_green_if_color_to_use_grey_as_is_green():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.GREY)
    dice.value = 4
    grey_board_part.add_dice(dice, [], color_to_use_grey_as=DiceColor.GREEN)
    assert all(not box.is_crossed for box in grey_board_part.boxes)


def test_add_dice_adds_white_dice_as_green_if_color_to_use_white_as_is_green():
    grey_board_part = GreyBoardPart()
    dice = Dice(DiceColor.WHITE)
    dice.value = 4
    grey_board_part.add_dice(dice, [], color_to_use_white_as=DiceColor.GREEN)
    assert all(not box.is_crossed for box in grey_board_part.boxes)


def test_add_dice_has_no_effect_if_die_is_already_crossed():
    grey_board_part = GreyBoardPart()
    yellow_box = next(
        box for box in grey_board_part.boxes
        if box.color == DiceColor.YELLOW and box.number == 3
    )
    yellow_box.is_crossed = True

    dice = Dice(DiceColor.GREY)
    dice.value = 5
    smaller = Dice(DiceColor.YELLOW)
    smaller.value = 3
    grey_board_part.add_dice(dice, [smaller], color_to_use_grey_as=DiceColor.BLUE)

    assert sum(1 for box in grey_board_part.boxes if box.is_crossed) == 1


def test_plus_one_action_returned_when_all_ones_are_crossed():
    grey_board_part = GreyBoardPart()
    for box in grey_board_part.boxes:
        if box.number == 1:
            box.is_crossed = True

    actions = grey_board_part._calculate_actions_received_in_round()
    assert ActionType.PLUS_ONE in actions


def test_plus_one_action_returned_only_once():
    grey_board_part = GreyBoardPart()
    for box in grey_board_part.boxes:
        if box.number == 1:
            box.is_crossed = True

    grey_board_part._calculate_actions_received_in_round()
    second_actions = grey_board_part._calculate_actions_received_in_round()

    assert ActionType.PLUS_ONE not in second_actions


def test_get_color_to_use_as_returns_original_color_for_non_special_die():
    grey_board_part = GreyBoardPart()
    die = Dice(DiceColor.YELLOW)
    assert grey_board_part._get_color_to_use_as(die, None, None) == DiceColor.YELLOW


def test_get_color_to_use_as_returns_substitute_color_for_white_die():
    grey_board_part = GreyBoardPart()
    die = Dice(DiceColor.WHITE)
    assert grey_board_part._get_color_to_use_as(die, DiceColor.BLUE, None) == DiceColor.BLUE


def test_get_color_to_use_as_returns_substitute_color_for_grey_die():
    grey_board_part = GreyBoardPart()
    die = Dice(DiceColor.GREY)
    assert grey_board_part._get_color_to_use_as(die, None, DiceColor.YELLOW) == DiceColor.YELLOW


def test_evaluate_returns_zero_for_empty_board():
    grey_board_part = GreyBoardPart()
    assert grey_board_part.evaluate() == 0


def test_evaluate_returns_correct_score_for_crossed_boxes():
    grey_board_part = GreyBoardPart()
    for box in grey_board_part.boxes[:3]:
        box.is_crossed = True
    assert grey_board_part.evaluate() == 7
