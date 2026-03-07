import logging

from src.dice.dice import DiceColor


class GreyBox:  # pylint: disable=too-few-public-methods
    def __init__(self, color: DiceColor, number: int) -> None:
        logging.debug("Initializing a grey box")
        self._validate_input(color, number)
        self.color = color
        self.number = number
        self.is_crossed = False

    @staticmethod
    def _validate_input(color: DiceColor, number: int) -> None:
        if not 1 <= number <= 6:
            message = "Number must be between 1 and 6"
            logging.error(message)
            raise ValueError(message)

        if color not in DiceColor:
            valid_colors = [color.value for color in DiceColor]
            message = "Color must be one of the following: " + ", ".join(valid_colors)
            logging.error(message)
            raise ValueError(message)

    def cross_box(self, dice_color: DiceColor,  dice_value: int) -> None:
        if dice_value == self.number and dice_color == self.color:
            self.is_crossed = True
            logging.info(f"Grey box for {self.color} | {self.number} crossed")
            return
        logging.info(
            f"Dice value {dice_value} and dice color {dice_color} do not match "
            f"for grey box {self.color} | {self.number}")

    def __str__(self) -> str:
        return (
            f"Grey box: {self.color.value} | {self.number} | crossed: {self.is_crossed}"
        )
