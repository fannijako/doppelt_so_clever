import logging
import random

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_handler import ActionHandler


class PassiveRound:  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        board: Board,
        action_handler: ActionHandler,
        automatic: bool = True,
    ):
        self.board = board
        self.action_handler = action_handler
        self.automatic = automatic

        self.dice_by_color: dict[DiceColor, Dice] = {
            color: Dice(color) for color in DiceColor
        }

    def execute(self) -> None:
        logging.info("-" * 100)
        logging.info("Starting passive player turn")

        all_dice = list(self.dice_by_color.values())
        for die in all_dice:
            die.roll()
        logging.info(f"Passive turn rolled dice: {', '.join(str(die) for die in all_dice)}")

        eligible_dice = self._get_lowest_n_dice(all_dice, 3)
        logging.info(f"Eligible dice (3 lowest): {', '.join(str(die) for die in eligible_dice)}")

        if not eligible_dice:
            logging.info("No eligible dice for passive turn")
            return

        if self.automatic:
            picked = random.choice(eligible_dice)
        else:
            logging.info(f"Pick one: {', '.join(f'{i}: {die}' for i, die in enumerate(eligible_dice))}")
            index = int(input('Pick a die index: '))
            picked = eligible_dice[index]

        logging.info(f"Passive turn picked die: {picked}")
        actions = self._get_actions(picked)
        self.action_handler.execute(actions, self.automatic)

    def _get_actions(self, picked: Dice) -> list[Action]:
        dispatch = {
            DiceColor.BLUE: lambda: self.board.blue_board_part.add_dice(
                picked, self.dice_by_color[DiceColor.WHITE]
            ),
            DiceColor.PINK: lambda: self.board.pink_board_part.add_dice(picked),
            DiceColor.GREEN: lambda: self.board.green_board_part.add_dice(picked),
            DiceColor.GREY: lambda: self.board.grey_board_part.place_dice(picked, self.automatic),
            DiceColor.YELLOW: lambda: self.board.yellow_board_part.place_dice(picked, self.automatic),
            DiceColor.WHITE: lambda: self.board.place_white_dice(picked, self.automatic, self.dice_by_color),
        }
        handler = dispatch.get(picked.color)
        if not handler:
            return []
        result = handler()
        return result if isinstance(result, list) else [result] if result else []

    @staticmethod
    def _get_lowest_n_dice(dice: list[Dice], n: int) -> list[Dice]:
        if len(dice) <= n:
            return list(dice)

        sorted_values = sorted(set(die.value for die in dice))
        selected: list[Dice] = []

        for value in sorted_values:
            dice_with_value = [die for die in dice if die.value == value and die not in selected]
            if len(selected) + len(dice_with_value) <= n:
                selected.extend(dice_with_value)
            else:
                remaining_slots = n - len(selected)
                selected.extend(random.sample(dice_with_value, remaining_slots))
                break

        return selected
