import logging
from typing import Optional

from src.actions.action_type import ActionType

logger = logging.getLogger(__name__)
from src.actions.action_map import ActionMap
from src.actions.base_action import Action
from src.board.boxes.blue_box import BlueBox
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor


class BlueBoardPart:
    def __init__(self) -> None:
        logger.debug("Initializing a blue board part")
        self.boxes: list[BlueBox] = [
            BlueBox(12, ActionType.NONE),
            BlueBox(12, ActionType.REUSE),
            BlueBox(12, ActionType.YELLOW_QUESTION_MARK),
            BlueBox(12, ActionType.NONE),
            BlueBox(12, ActionType.PLUS_ONE),
            BlueBox(12, ActionType.REROLL),
            BlueBox(12, ActionType.PINK_QUESTION_MARK),
            BlueBox(12, ActionType.NONE),
            BlueBox(12, ActionType.FOX),
            BlueBox(12, ActionType.REUSE),
            BlueBox(12, ActionType.NONE),
            BlueBox(12, ActionType.GREEN_QUESTION_MARK),
        ]

    def get_value_limit_on_next_box(self) -> int:
        for box in self.boxes:
            if box.value_used is None:
                return box.maximum_value_limit
        return 0

    def add_dice(self, blue_dice: Dice, white_dice: Dice) -> Optional[Action]:
        self._validate_dice(blue_dice, white_dice)
        logger.info(f'Adding dice {str(blue_dice)} to blue board part with {str(white_dice)}')

        for index, current_blue_box in enumerate(self.boxes):
            if current_blue_box.value_used is None:
                current_blue_box.add_dice_value(blue_dice.value, white_dice.value)

                if current_blue_box.value_used is None:
                    logger.info(f'Dice sum exceeds limit on blue box {index}, skipping placement')
                    return None

                logger.info(f'Added dice {str(blue_dice)} to blue box {index}')

                for following_box in self.boxes[index + 1:]:
                    following_box.maximum_value_limit = current_blue_box.value_used
                logger.info(f'Lowered following boxes upper limits to {current_blue_box.value_used}')

                return ActionMap.get(current_blue_box.action)

        raise ValueError("No free blue box available to add dice")

    @staticmethod
    def _validate_dice(blue_dice: Dice, white_dice: Dice) -> None:
        if blue_dice.color != DiceColor.BLUE or white_dice.color != DiceColor.WHITE:
            message = "Attempted to add a dice of a different color to blue board part"
            logger.warning(message)
            raise ValueError(message)

        if blue_dice.value is None or white_dice.value is None:
            message = "Attempted to add an unrolled dice to blue board part"
            logger.warning(message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        point_dice_number_map = {
            0: 0,
            1: 1,
            2: 3,
            3: 6,
            4: 10,
            5: 15,
            6: 21,
            7: 28,
            8: 36,
            9: 45,
            10: 55,
            11: 66,
            12: 78,
        }
        number_of_boxes_used = len([box for box in self.boxes if box.value_used is not None])
        return point_dice_number_map.get(number_of_boxes_used, 0)
