import os

import pytest
import pygame

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor


@pytest.fixture(scope="session")
def display_screen():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    yield screen
    pygame.quit()


@pytest.fixture
def build_die():
    def _build(color: DiceColor, value: int) -> Dice:
        die = Dice(color)
        die.set_value(value)
        return die
    return _build
