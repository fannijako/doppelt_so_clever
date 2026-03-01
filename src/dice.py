from enum import Enum
import random
import logging


class DiceColor(Enum):
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    YELLOW = "yellow"
    GREY = "grey"
    PINK = "pink"


class Dice:
    def __init__(self, color: DiceColor) -> None:
        logging.debug(f"Initializing a dice with {color}")
        self.color = color
        self.value = None

    def roll(self) -> None:
        self.value = random.randint(1, 6)
        logging.debug(f"{self.color.value} dice rolled: {self.value}")

    def __str__(self) -> str:
        if self.value is None:
            return f"{self.color.value}: Unrolled"
        return f"{self.color.value}: {self.value}"
