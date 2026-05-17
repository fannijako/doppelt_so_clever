import pytest

from src.board.board import Board
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.game.rl_observer import RLObserver, DecisionType


@pytest.fixture()
def observer():
    return RLObserver(Board(), augmented=False)


@pytest.fixture()
def default_context():
    return RLObserver(Board(), augmented=False).get_context_tensor(DecisionType.CHOOSE_INDEX, 5)


@pytest.fixture()
def six_dice():
    dice = []
    for i, color in enumerate(DiceColor, start=1):
        die = Dice(color)
        die.value = i
        dice.append(die)
    return dice
