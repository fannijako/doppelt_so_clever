from enum import Enum
import random


class Color(Enum):
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    YELLOW = "yellow"
    GREY = "grey"
    PINK = "pink"


class Die:
    def __init__(self, color: Color) -> None:
        self.color = color
        self.value = None

    def roll(self) -> None:
        self.value = random.randint(1, 6)

    def __str__(self) -> str:
        if self.value is None:
            return f"{self.color}: Unrolled"
        return f"{self.color}: {self.value}"
