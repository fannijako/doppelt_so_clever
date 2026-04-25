import random
from typing import Optional

from src.actions.action_map import ActionMap
from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.boxes.grey_box import GreyBox
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class GreyBoardPart:
    _SUBSTITUTABLE_COLORS = [DiceColor.YELLOW, DiceColor.BLUE, DiceColor.PINK, DiceColor.GREEN]

    def __init__(self):
        logger.debug("Init", "grey board part")
        self.boxes = [
            GreyBox(color=color, number=number)
            for color in [
                DiceColor.YELLOW,
                DiceColor.BLUE,
                DiceColor.BLUE,
                DiceColor.PINK,
            ]
            for number in range(1, 7)
        ]
        self._available_columns_for_action = {
            1: ActionType.PLUS_ONE,
            2: ActionType.YELLOW_QUESTION_MARK,
            3: ActionType.FOX,
            4: ActionType.BLUE_QUESTION_MARK,
            5: ActionType.GREEN_QUESTION_MARK,
            6: ActionType.PINK_QUESTION_MARK,
        }

    def add_dice(
        self,
        dice: Dice,
        smaller_die: list[Dice],
        color_to_use_white_as: Optional[DiceColor] = None,
        color_to_use_grey_as: Optional[DiceColor] = None,
    ) -> list[Action]:

        self._validate_dice(dice)
        self._validate_smaller_die(dice, smaller_die)
        self._validate_color_changes(dice, smaller_die, color_to_use_white_as, color_to_use_grey_as)
        all_die = [dice] + smaller_die
        logger.info(
            "Grey board",
            " + ".join(str(die) for die in all_die),
            f"white as {color_to_use_white_as}, grey as {color_to_use_grey_as}",
        )

        for die in all_die:
            value = die.value
            color = self._get_color_to_use_as(die, color_to_use_white_as, color_to_use_grey_as)
            box_to_cross = [box for box in self.boxes if box.color == color and box.number == value and not box.is_crossed]
            if not box_to_cross:
                logger.info("Grey box", f"{die.color} | {die.value}", "no box to cross")
                continue
            box_to_cross[0].cross_box(color, die.value)

        return self._calculate_actions_received_in_round()

    def place_dice(
        self,
        dice: Dice,
        automatic: bool,
        smaller_die: list[Dice] = None,
    ) -> list[Action]:
        if smaller_die is None:
            smaller_die = []

        all_die = [dice] + smaller_die
        has_white = any(die.color == DiceColor.WHITE for die in all_die)
        has_grey = any(die.color == DiceColor.GREY for die in all_die)

        color_to_use_white_as = None
        if has_white:
            color_to_use_white_as = (
                random.choice(self._SUBSTITUTABLE_COLORS) if automatic
                else DiceColor(input('Pick an available color to substitute white as: '))
            )

        color_to_use_grey_as = None
        if has_grey:
            color_to_use_grey_as = (
                random.choice(self._SUBSTITUTABLE_COLORS) if automatic
                else DiceColor(input('Pick an available color to substitute grey as: '))
            )

        return self.add_dice(
            dice=dice,
            smaller_die=smaller_die,
            color_to_use_white_as=color_to_use_white_as,
            color_to_use_grey_as=color_to_use_grey_as,
        )

    def _calculate_actions_received_in_round(self) -> list[Action]:
        actions_received = []

        for value in range(1, 7):
            boxes_with_value = [box for box in self.boxes if box.number == value and box.is_crossed]
            if len(boxes_with_value) == 4 and value in self._available_columns_for_action:
                actions_received.append(ActionMap.get(self._available_columns_for_action[value]))
                self._available_columns_for_action.pop(value)

        return actions_received

    def _get_color_to_use_as(
        self,
        die: Dice,
        color_to_use_white_as: Optional[DiceColor],
        color_to_use_grey_as: Optional[DiceColor],
    ) -> DiceColor:

        if die.color not in [DiceColor.WHITE, DiceColor.GREY]:
            return die.color
        if die.color == DiceColor.WHITE:
            return color_to_use_white_as
        return color_to_use_grey_as

    def _validate_color_changes(
        self,
        dice: Dice,
        smaller_die: list[Dice],
        color_to_use_white_as: Optional[DiceColor] = None,
        color_to_use_grey_as: Optional[DiceColor] = None,
    ) -> None:

        die_colors = [die.color for die in smaller_die] + [dice.color]
        if DiceColor.WHITE in die_colors and not color_to_use_white_as:
            message = "Attempted to add a white dice to grey board part without specifying a color to use white as"
            logger.warning("Validation", message)
            raise ValueError(message)

        if DiceColor.GREY in die_colors and not color_to_use_grey_as:
            message = "Attempted to add a grey dice to grey board part without specifying a color to use grey as"
            logger.warning("Validation", message)
            raise ValueError(message)

    def _validate_dice(self, dice: Dice) -> None:
        if dice.color not in [DiceColor.GREY, DiceColor.WHITE]:
            message = "Attempted to add a dice of a different color to grey board part"
            logger.warning("Validation", message)
            raise ValueError(message)

        if dice.value is None:
            message = "Attempted to add an unrolled dice to grey board part"
            logger.warning("Validation", message)
            raise ValueError(message)

    def _validate_smaller_die(self, dice: Dice, smaller_die: list[Dice]) -> None:
        for smaller_dice in smaller_die:
            if smaller_dice.value is None:
                message = "Attempted to add an unrolled dice to grey board part"
                logger.warning("Validation", message)
                raise ValueError(message)

            if smaller_dice.color == dice.color:
                message = "Attempted to add a dice of the same color to grey board part"
                logger.warning("Validation", message)
                raise ValueError(message)

            if smaller_dice.value >= dice.value:
                message = "Attempted to add a dice with greater or equal value to grey board part"
                logger.warning("Validation", message)
                raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        return sum(
            self._crossed_box_to_points(
                len([
                    box for box in row if box.is_crossed
                ])
            )
            for row in [self.boxes[i:i+6] for i in range(0, len(self.boxes), 6)]
        )

    def _crossed_box_to_points(self, number_of_crossed_boxes: int) -> int:
        crossed_box_to_points_map = {
            0: 0,
            1: 2,
            2: 4,
            3: 7,
            4: 11,
            5: 16,
            6: 22,
        }
        return crossed_box_to_points_map[number_of_crossed_boxes]
