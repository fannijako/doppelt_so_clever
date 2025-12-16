import pytest

from src.die import Die, DieColor


@pytest.fixture
def blue_and_white_dies():
    blue_die = Die(DieColor.BLUE)
    blue_die.value = 6
    white_die = Die(DieColor.WHITE)
    white_die.value = 6
    return blue_die, white_die
