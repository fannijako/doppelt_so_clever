import logging
import random
from typing import Optional

from src.dice import Dice, DiceColor
from src.board import Board
from src.actions import Action


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

    def pick_die(self) -> Optional[tuple[Dice, list[Dice]]]:
        color = self.pick_dice_color()
        dice = [dice for dice in self.available_die if str(dice.color.value) == color]

        picked_dice = dice[0] if dice else None
        if not picked_dice:
            return None
        picked_number = picked_dice.value
        smaller_die = [dice for dice in self.available_die if dice.value < picked_number]
        self.available_die.remove(picked_dice)
        self.picked_die.append(picked_dice)
        self.discarded_die.extend(smaller_die)

        logging.info(f"Picked die: {picked_dice}")
        logging.info(f"Available dice left: {[str(dice) for dice in self.available_die]}")
        logging.info(f"Discarded dice: {[str(dice) for dice in self.discarded_die]}")
        return picked_dice, smaller_die

    def execute(self):
        for game_round in range(1, 4):
            logging.info(f'Starting round {game_round}')
            self.roll_die()

            actions = []
            picked_die, smaller_die = self.pick_die()
            if picked_die.color == DiceColor.BLUE:
                actions.append(self.board.blue_board_part.add_dice(picked_die, self.white_dice))
            if picked_die.color == DiceColor.PINK:
                actions.append(self.board.pink_board_part.add_dice(picked_die))
            if picked_die.color == DiceColor.GREEN:
                actions.append(self.board.green_board_part.add_dice(picked_die))
            if picked_die.color == DiceColor.GREY:
                actions.append(self.place_a_grey_dice(picked_die, smaller_die))
            if picked_die.color == DiceColor.YELLOW:
                actions.append(self.place_a_yellow_dice(picked_die))
            if picked_die.color == DiceColor.WHITE:
                actions.append(self.place_a_white_dice(picked_die, self.blue_dice))

            logging.info(f"Actions received in round {game_round}: {actions}")

    def place_a_grey_dice(self, dice: Dice, smaller_die: list[Dice]) -> list[Action]:
        if DiceColor.WHITE in [dice.color for dice in smaller_die]:
            use_white_as = random.choice(
                [DiceColor.BLUE, DiceColor.GREEN, DiceColor.PINK, DiceColor.YELLOW]
            ) if self.automatic else input('Pick an available color to substitute white as: ')
        else:
            use_white_as = None

        use_grey_as = random.choice(
            [DiceColor.BLUE, DiceColor.GREEN, DiceColor.PINK, DiceColor.YELLOW]
            ) if self.automatic else input('Pick an available color to substitute grey as: ')

        return self.board.grey_board_part.add_dice(
            dice=dice,
            smaller_die=smaller_die,
            color_to_use_white_as=use_white_as,
            color_to_use_grey_as=use_grey_as
        )

    def place_a_yellow_dice(self, dice: Dice) -> list[Action]:
        possible_dice_placements = self.board.yellow_board_part.possible_dice_placements(dice)
        logging.info(f'Possible dice placements: {possible_dice_placements}')

        if len(possible_dice_placements) == 0:
            return []
        if len(possible_dice_placements) == 1:
            return self.board.yellow_board_part.add_dice(
                dice=dice,
                row_position=possible_dice_placements[0][0],
                column_position=possible_dice_placements[0][1],
                action=possible_dice_placements[0][2]
            )
        if self.automatic:
            dice_placement = random.choice(possible_dice_placements)
            return self.board.yellow_board_part.add_dice(
                dice=dice,
                row_position=dice_placement[0],
                column_position=dice_placement[1],
                action=dice_placement[2]
            )

        row_position = int(input('Pick a row position: '))
        column_position = int(input('Pick a column position: '))
        action = input('Pick an action: ')
        return self.board.yellow_board_part.add_dice(
            dice=dice,
            row_position=row_position,
            column_position=column_position,
            action=action
        )

    def place_a_white_dice(self, dice: Dice, blue_dice: Dice) -> list[Action]:
        if self.automatic:
            play_white_as = random.choice(
                [
                    DiceColor.BLUE,
                    DiceColor.GREEN,
                    DiceColor.PINK,
                    DiceColor.YELLOW,
                    DiceColor.GREY
                ]
            )
        else:
            play_white_as = DiceColor(input('Pick an available color to play white as: '))

        if play_white_as == DiceColor.BLUE:
            return self.board.blue_board_part.add_dice(blue_dice, dice)
        if play_white_as == DiceColor.GREEN:
            return self.board.green_board_part.add_dice(dice)
        if play_white_as == DiceColor.PINK:
            return self.board.pink_board_part.add_dice(dice)
        if play_white_as == DiceColor.YELLOW:
            return self.place_a_yellow_dice(dice)
        return self.place_a_grey_dice(dice, [])
