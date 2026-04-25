from src.actions.action_map import ActionMap
from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.boxes.green_box import GreenBox
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class GreenBoardPart:
    def __init__(self) -> None:
        logger.debug("Init", "green board part")
        self.boxes: list[GreenBox] = [
            GreenBox(2, ActionType.NONE, 0),
            GreenBox(2, ActionType.REROLL, 1),
            GreenBox(2, ActionType.NONE, 2),
            GreenBox(1, ActionType.BLUE_QUESTION_MARK, 3),
            GreenBox(3, ActionType.REUSE, 4),
            GreenBox(3, ActionType.NONE, 5),
            GreenBox(3, ActionType.FOX, 6),
            GreenBox(2, ActionType.GREY_QUESTION_MARK, 7),
            GreenBox(3, ActionType.PLUS_ONE, 8),
            GreenBox(1, ActionType.NONE, 9),
            GreenBox(4, ActionType.PINK_QUESTION_MARK, 10),
            GreenBox(1, ActionType.YELLOW_QUESTION_MARK, 11),
        ]

    def add_dice(self, dice: Dice) -> Action:
        self._validate_dice(dice)
        logger.info("Green board", dice, "adding")
        index_of_next_empty_field = self.index_of_next_empty_field()
        box = self.boxes[index_of_next_empty_field]
        box.add_dice_value(dice.value)
        logger.info("Green box", f"{dice} at {index_of_next_empty_field}: {box.value_used}", "added")
        return ActionMap.get(box.action)

    def index_of_next_empty_field(self) -> int:
        empty_boxes = list(filter(lambda box: box.value_used is None, self.boxes))
        if not empty_boxes:
            logger.warning("Green board", "no free box")
            return 12
        return min(empty_boxes, key=lambda box: box.index).index

    def sign_of_next_empty_field(self) -> int:
        return 1 if self.index_of_next_empty_field() % 2 == 0 else -1

    @staticmethod
    def _validate_dice(dice: Dice) -> None:
        if dice.color not in [DiceColor.GREEN, DiceColor.WHITE]:
            message = "Attempted to add a dice of a different color to green board part"
            logger.warning("Validation", message)
            raise ValueError(message)

        if dice.value is None:
            message = "Attempted to add an unrolled dice to green board part"
            logger.warning("Validation", message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        used_boxes = list(filter(lambda box: box.value_used is not None, self.boxes))

        if len(used_boxes) % 2 != 0:
            used_boxes.pop()

        return sum(
            box.value_used if box.index % 2 == 0 else -box.value_used
            for box in used_boxes
        )
