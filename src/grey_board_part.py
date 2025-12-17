from src.grey_box import GreyBox


class GreyBoardPart:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.boxes = [GreyBox() for _ in range(6)]

    def evaluate(self) -> int:
        return 0
