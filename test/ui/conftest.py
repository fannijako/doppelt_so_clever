import pytest
import arcade

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor


@pytest.fixture
def build_die():
    def _build(color: DiceColor, value: int) -> Dice:
        die = Dice(color)
        die.set_value(value)
        return die
    return _build


@pytest.fixture(scope="session")
def arcade_window():
    try:
        window = arcade.Window(1280, 800, "test", visible=False)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        pytest.skip(f"no OpenGL context available: {exc}")
    yield window
    window.close()
