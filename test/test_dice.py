from src.dice import Dice


def test_dice_color():
    dice = Dice("pink")
    assert dice.color == "pink"


def test_unrolled_dice():
    dice = Dice("pink")
    assert not dice.value


def test_rolled_dice():
    dice = Dice("pink")
    dice.roll()
    assert dice.value is not None
    assert dice.value >= 1
    assert dice.value <= 6


def test_dice_str():
    dice = Dice("pink")
    assert str(dice) == "pink: Unrolled"
