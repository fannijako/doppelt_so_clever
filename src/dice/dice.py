import random

from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class Dice:
    def __init__(self, color: DiceColor) -> None:
        logger.debug("Init dice", color)
        self.color = color
        self.value = None

    def set_value(self, value: int) -> None:
        if not 1 <= value <= 6:
            raise ValueError("Dice value must be between 1 and 6")
        self.value = value

    def roll(self) -> None:
        self.value = random.randint(1, 6)
        logger.debug("Dice rolled", f"{self.color.value}: {self.value}")

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if self.value is None:
            return f"{self.color.value}: Unrolled"
        return f"{self.color.value}: {self.value}"
