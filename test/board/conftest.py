import pytest

from src.board.board import Board
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor


@pytest.fixture()
def empty_board():
    return Board()


@pytest.fixture()
def empty_tensor():
    return Board().to_tensor()


@pytest.fixture()
def filled_blue_board():
    board = Board()
    blue_dice = Dice(DiceColor.BLUE)
    blue_dice.value = 4
    white_dice = Dice(DiceColor.WHITE)
    white_dice.value = 3
    board.blue_board_part.add_dice(blue_dice, white_dice)
    return board
