import logging
import random
from typing import Optional

from src.dice import Dice, DiceColor
from src.board import Board


class ActiveRound:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(
        self,
        board: Board,
        automatic: bool = True
    ):
        self.board = board
        self.automatic = automatic

        self.blue_dice = Dice(DiceColor.BLUE)
        self.white_dice = Dice(DiceColor.WHITE)
        self.pink_dice = Dice(DiceColor.PINK)
        self.green_dice = Dice(DiceColor.GREEN)
        self.grey_dice = Dice(DiceColor.GREY)
        self.yellow_dice = Dice(DiceColor.YELLOW)
        self.die = [
            self.blue_dice,
            self.white_dice,
            self.pink_dice,
            self.green_dice,
            self.grey_dice,
            self.yellow_dice
        ]
        self.available_die = self.die.copy()
        self.picked_die = []
        self.discarded_die = []

    def roll_die(self):
        for dice in self.die:
            dice.roll()
        logging.info(f"ActiveRound: {str(self)}")

    def __str__(self):
        return "\n".join([str(dice) for dice in self.die])

    def pick_dice_color(self):
        colors = [str(dice.color.value) for dice in self.available_die]
        logging.info(f'Available dice colors: {", ".join(colors)}')

        color = random.choice(colors) if self.automatic else input('Pick an available color: ')
        logging.info(f'Picked color: {color}')
        return color

    def pick_die(self) -> Optional[Dice]:
        color = self.pick_dice_color()
        dice = [dice for dice in self.available_die if str(dice.color.value) == color]

        picked_dice = dice[0] if dice else None
        if not picked_dice:
            return None
        picked_number = picked_dice.value
        self.available_die.remove(picked_dice)
        self.picked_die.append(picked_dice)
        self.discarded_die.extend(
            [dice for dice in self.available_die
             if dice.value < picked_number]
        )

        logging.info(f"Picked die: {picked_dice}")
        logging.info(f"Available dice left: {[str(dice) for dice in self.available_die]}")
        logging.info(f"Discarded dice: {[str(dice) for dice in self.discarded_die]}")
        return picked_dice

    def execute(self):
        for game_round in range(1, 4):
            logging.info(f'Starting round {game_round}')
            self.roll_die()

            picked_die = self.pick_die()
            if picked_die.color == DiceColor.PINK:
                self.board.pink_board_part.add_dice(picked_die)
            if picked_die.color == DiceColor.GREEN:
                self.board.green_board_part.add_dice(picked_die)
            if picked_die.color == DiceColor.BLUE:
                self.board.blue_board_part.add_dice(picked_die, self.white_dice)
