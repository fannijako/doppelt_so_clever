from src.dice.dice import Dice
from src.dice.dice_color import DiceColor


def test_dice_color():
    dice = Dice(DiceColor.PINK)
    assert dice.color.value == "pink"


def test_unrolled_dice():
    dice = Dice(DiceColor.PINK)
    assert not dice.value


def test_rolled_dice():
    dice = Dice(DiceColor.PINK)
    dice.roll()
    assert dice.value is not None
    assert dice.value >= 1
    assert dice.value <= 6


def test_dice_str():
    dice = Dice(DiceColor.PINK)
    assert str(dice) == "pink: Unrolled"
