from typing import Optional

from src.actions.action_map import ActionMap
from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.boxes.pink_box import PinkBox
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class PinkBoardPart:  # pylint: disable=too-few-public-methods
    def __init__(self) -> None:
        logger.debug("Init", "pink board part")
        self.boxes: list[PinkBox] = [
            PinkBox(0, ActionType.NONE),
            PinkBox(0, ActionType.NONE),
            PinkBox(2, ActionType.REROLL),
            PinkBox(3, ActionType.REUSE),
            PinkBox(4, ActionType.PLUS_ONE),
            PinkBox(5, ActionType.GREEN_QUESTION_MARK),
            PinkBox(6, ActionType.YELLOW_QUESTION_MARK),
            PinkBox(2, ActionType.FOX),
            PinkBox(3, ActionType.GREY_QUESTION_MARK),
            PinkBox(4, ActionType.REROLL),
            PinkBox(5, ActionType.BLUE_QUESTION_MARK),
            PinkBox(6, ActionType.YELLOW_QUESTION_MARK),
        ]

    def add_dice(self, dice: Dice) -> Optional[Action]:
        self._validate_dice(dice)
        logger.info("Pink board", dice, "adding")

        for index, pink_box in enumerate(self.boxes):
            if pink_box.value_used is None:
                pink_box.add_dice_value(dice.value)
                logger.info("Pink box", f"{dice} at {index}", "added")
                return ActionMap.get(pink_box.action) if dice.value >= pink_box.action_filter_limit else None

        raise ValueError("No free pink box available to add dice")

    @staticmethod
    def _validate_dice(dice: Dice) -> None:
        if dice.color not in [DiceColor.PINK, DiceColor.WHITE]:
            message = "Attempted to add a dice of a different color to pink board part"
            logger.warning("Validation", message)
            raise ValueError(message)

        if dice.value is None:
            message = "Attempted to add an unrolled dice to pink board part"
            logger.warning("Validation", message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        return sum(box.value_used for box in self.boxes if box.value_used is not None)
