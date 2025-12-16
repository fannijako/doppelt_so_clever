from enum import Enum
import random
import logging


class DieColor(Enum):
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    YELLOW = "yellow"
    GREY = "grey"
    PINK = "pink"


class Die:
    def __init__(self, color: DieColor) -> None:
        logging.debug(f"Initializing a die with {color}")
        self.color = color
        self.value = None

    def roll(self) -> None:
        self.value = random.randint(1, 6)
        logging.info(f"{self.color} die rolled: {self.value}")

    def __str__(self) -> str:
        if self.value is None:
            return f"{self.color}: Unrolled"
        return f"{self.color}: {self.value}"
