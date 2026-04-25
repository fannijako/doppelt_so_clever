from src.dice.dice import DiceColor
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class GreyBox:  # pylint: disable=too-few-public-methods
    def __init__(self, color: DiceColor, number: int) -> None:
        logger.debug("Init", "grey box")
        self._validate_input(color, number)
        self.color = color
        self.number = number
        self.is_crossed = False

    @staticmethod
    def _validate_input(color: DiceColor, number: int) -> None:
        if not 1 <= number <= 6:
            message = "Number must be between 1 and 6"
            logger.error("Validation", message)
            raise ValueError(message)

        if color not in DiceColor:
            valid_colors = [color.value for color in DiceColor]
            message = "Color must be one of the following: " + ", ".join(valid_colors)
            logger.error("Validation", message)
            raise ValueError(message)

    def cross_box(self, dice_color: DiceColor,  dice_value: int) -> None:
        if dice_value == self.number and dice_color == self.color:
            self.is_crossed = True
            logger.info("Grey box", f"{self.color} | {self.number}", "crossed")
            return
        logger.info("Grey box", f"{self.color} | {self.number}", f"no match: {dice_color} {dice_value}")

    def __str__(self) -> str:
        return (
            f"Grey box: {self.color.value} | {self.number} | crossed: {self.is_crossed}"
        )
