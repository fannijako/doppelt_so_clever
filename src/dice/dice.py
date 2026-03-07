import random
import logging

from src.dice.dice_color import DiceColor


class Dice:
    def __init__(self, color: DiceColor) -> None:
        logging.debug(f"Initializing a dice with {color}")
        self.color = color
        self.value = None

    def set_value(self, value: int) -> None:
        if not 1 <= value <= 6:
            raise ValueError("Dice value must be between 1 and 6")
        self.value = value

    def roll(self) -> None:
        self.value = random.randint(1, 6)
        logging.debug(f"{self.color.value} dice rolled: {self.value}")

    def __str__(self) -> str:
        if self.value is None:
            return f"{self.color.value}: Unrolled"
        return f"{self.color.value}: {self.value}"
