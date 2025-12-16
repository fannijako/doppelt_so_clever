import pytest

from src.dice import Dice, DiceColor


@pytest.fixture
def blue_and_white_dices():
    blue_dice = Dice(DiceColor.BLUE)
    blue_dice.value = 6
    white_dice = Dice(DiceColor.WHITE)
    white_dice.value = 6
    return blue_dice, white_dice
