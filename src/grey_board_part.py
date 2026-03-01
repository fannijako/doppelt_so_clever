from src.grey_box import GreyBox
from src.dice import DiceColor


class GreyBoardPart:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.boxes = [
            GreyBox(color=color, number=number)
            for color in DiceColor
            for number in range(1, 7)
        ]

    def evaluate(self) -> int:
        return 0
