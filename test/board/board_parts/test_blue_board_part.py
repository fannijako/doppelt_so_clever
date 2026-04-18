import pytest

from src.board.board_parts.blue_board_part import BlueBoardPart
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.actions.action_type import ActionType
from src.actions.action_map import ActionMap


def test_add_dice_return_action_on_first_box(blue_and_white_dices):
    blue_board_part = BlueBoardPart()
    blue_dice, white_dice = blue_and_white_dices
    assert blue_board_part.add_dice(blue_dice, white_dice) == ActionMap.get(ActionType.NONE)


def test_add_dice_return_action_on_second_box(blue_and_white_dices):
    blue_board_part = BlueBoardPart()
    blue_dice, white_dice = blue_and_white_dices
    blue_board_part.add_dice(blue_dice, white_dice)
    assert blue_board_part.add_dice(blue_dice, white_dice) == ActionMap.get(ActionType.REUSE)


def test_add_dice_return_action_on_third_box(blue_and_white_dices):
    blue_board_part = BlueBoardPart()
    blue_dice, white_dice = blue_and_white_dices
    blue_board_part.add_dice(blue_dice, white_dice)
    blue_board_part.add_dice(blue_dice, white_dice)
    assert blue_board_part.add_dice(blue_dice, white_dice) == ActionMap.get(ActionType.YELLOW_QUESTION_MARK)


def test_fail_on_add_dice_with_different_color():
    with pytest.raises(ValueError):
        blue_board_part = BlueBoardPart()
        blue_dice = Dice(DiceColor.GREEN)
        blue_dice.roll()
        white_dice = Dice(DiceColor.WHITE)
        white_dice.roll()
        blue_board_part.add_dice(blue_dice, white_dice)


def test_fail_on_add_dice_with_unrolled_dice():
    with pytest.raises(ValueError):
        blue_board_part = BlueBoardPart()
        blue_dice = Dice(DiceColor.BLUE)
        white_dice = Dice(DiceColor.WHITE)
        blue_board_part.add_dice(blue_dice, white_dice)


def test_fail_on_add_dice_with_full_board(blue_and_white_dices):
    blue_board_part = BlueBoardPart()
    blue_dice, white_dice = blue_and_white_dices
    for _ in range(12):
        blue_board_part.add_dice(blue_dice, white_dice)

    with pytest.raises(ValueError):
        blue_board_part.add_dice(blue_dice, white_dice)


def test_add_dice_skips_placement_when_sum_exceeds_limit():
    blue_board_part = BlueBoardPart()
    blue_dice = Dice(DiceColor.BLUE)
    white_dice = Dice(DiceColor.WHITE)
    blue_dice.value = 1
    white_dice.value = 1
    blue_board_part.add_dice(blue_dice, white_dice)

    blue_dice.value = 6
    white_dice.value = 6
    result = blue_board_part.add_dice(blue_dice, white_dice)

    assert result is None
    assert blue_board_part.boxes[1].value_used is None
    assert blue_board_part.boxes[2].maximum_value_limit == 2


def test_evaluate(blue_and_white_dices):
    blue_board_part = BlueBoardPart()
    blue_dice, white_dice = blue_and_white_dices
    assert blue_board_part.evaluate() == 0

    blue_board_part.add_dice(blue_dice, white_dice)
    assert blue_board_part.evaluate() == 1

    blue_board_part.add_dice(blue_dice, white_dice)
    assert blue_board_part.evaluate() == 3
