import pytest

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor


@pytest.fixture
def blue_and_white_dices():
    blue_dice = Dice(DiceColor.BLUE)
    blue_dice.value = 6
    white_dice = Dice(DiceColor.WHITE)
    white_dice.value = 6
    return blue_dice, white_dice
