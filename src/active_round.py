import logging

from src.dice import Dice, DiceColor
from src.board import Board


class ActiveRound:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(
        self,
        board: Board
    ):
        self.board = board
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
            self.green_dice,
            self.grey_dice,
            self.yellow_dice
        ]

    def roll_die(self):
        for dice in self.die:
            dice.roll()
        logging.info(f"ActiveRound: {str(self)}")

    def __str__(self):
        return "\n".join([str(dice) for dice in self.die])

    def execute(self) -> Board:

        self.roll_die()
        try:
            self.board.blue_board_part.add_dice(self.blue_dice, self.white_dice)
        except ValueError as e:
            logging.error(e)
        self.board.green_board_part.add_dice(self.green_dice)
        self.board.pink_board_part.add_dice(self.pink_dice)

        return self.board
