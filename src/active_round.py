from src.dice import Dice, DiceColor


class ActiveRound:  # pylint: disable=too-few-public-methods
    def __init__(self):
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
