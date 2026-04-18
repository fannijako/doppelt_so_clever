import logging
import random
from typing import Optional

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.board.board import Board
from src.actions.base_action import Action
from src.actions.action_handler import ActionHandler
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction


class ActiveRound:
    _NUM_ROUNDS = 3

    def __init__(
        self,
        board: Board,
        action_handler: ActionHandler,
        automatic: bool = True,
    ):
        self.board = board
        self.automatic = automatic
        self.action_handler = action_handler

        self.dice_by_color: dict[DiceColor, Dice] = {
            color: Dice(color) for color in DiceColor
        }
        self.available_dice: list[Dice] = list(self.dice_by_color.values())
        self.picked_dice: list[Dice] = []
        self.discarded_dice: list[Dice] = []

    def roll_dice(self) -> None:
        for die in self.available_dice:
            die.roll()
        logging.info(f"ActiveRound: {self}")

    def __str__(self) -> str:
        sections = [
            ("Available dice", self.available_dice),
            ("Picked dice", self.picked_dice),
            ("Discarded dice", self.discarded_dice),
        ]
        return "\n".join(
            f"{label}:\n" + "\n".join(str(die) for die in dice)
            for label, dice in sections
        )

    def _pick_color(self) -> str:
        colors = [str(die.color.value) for die in self.available_dice]
        logging.info(f'Available dice colors: {", ".join(colors)}')

        color = random.choice(colors) if self.automatic else input('Pick an available color: ')
        logging.info(f'Picked color: {color}')
        return color

    def pick_die(self) -> Optional[tuple[Dice, list[Dice]]]:
        color = self._pick_color()
        matched = [die for die in self.available_dice if str(die.color.value) == color]

        if not matched:
            return None

        picked = matched[0]
        smaller = [die for die in self.available_dice if die.value < picked.value]
        self.available_dice.remove(picked)
        for die in smaller:
            self.available_dice.remove(die)
        self.picked_dice.append(picked)
        self.discarded_dice.extend(smaller)

        logging.info(f"Picked die: {picked}")
        logging.info(f"ActiveRound: {self}")
        return picked, smaller

    def _get_actions(self, picked: Dice, smaller: list[Dice]) -> list[Action]:
        dispatch = {
            DiceColor.BLUE: lambda: self.board.blue_board_part.add_dice(
                picked, self.dice_by_color[DiceColor.WHITE]
            ),
            DiceColor.PINK: lambda: self.board.pink_board_part.add_dice(picked),
            DiceColor.GREEN: lambda: self.board.green_board_part.add_dice(picked),
            DiceColor.GREY: lambda: self.board.grey_board_part.place_dice(picked, self.automatic, smaller),
            DiceColor.YELLOW: lambda: self.board.yellow_board_part.place_dice(picked, self.automatic),
            DiceColor.WHITE: lambda: self.board.place_white_dice(picked, self.automatic, self.dice_by_color, smaller),
        }
        handler = dispatch.get(picked.color)
        if not handler:
            return []
        result = handler()
        return result if isinstance(result, list) else [result] if result else []

    def _try_reuse(self) -> None:
        logging.info(f"Usable reuses: {self.board.usable_reuses}, discarded dice: {len(self.discarded_dice)}")
        while self.board.usable_reuses > 0 and self.discarded_dice:
            if self.automatic:
                should_use = random.choice([True, False])
            else:
                should_use = input('Use a reuse? (y/n): ').lower() == 'y'

            if not should_use:
                logging.info("Chose not to use reuse")
                break

            chosen_die = ReUseAction().use(
                self.board, self.automatic,
                discarded_dice=self.discarded_dice,
            )
            if chosen_die is not None:
                self.discarded_dice.remove(chosen_die)
                self.available_dice.append(chosen_die)
                logging.info(f"Moved {chosen_die} from discarded to available dice")

    def _try_reroll(self) -> None:
        logging.info(f"Usable rerolls: {self.board.usable_rerolls}")
        while self.board.usable_rerolls > 0:
            if self.automatic:
                should_use = random.choice([True, False])
            else:
                should_use = input('Use a reroll? (y/n): ').lower() == 'y'

            if not should_use:
                logging.info("Chose not to use reroll")
                break

            logging.info(f"Using reroll (remaining after use: {self.board.usable_rerolls - 1})")
            ReRollAction().use(self.board, self.automatic)
            self.roll_dice()

    def _ask_to_place_die(self, picked: Dice) -> bool:
        if self.automatic:
            return random.choice([True, False])
        else:
            response = input(f'Place die {picked}? (y/n): ').lower()
            should_place = response == 'y'
            logging.info(f"Chose to {'place' if should_place else 'skip'} die {picked}")
            return should_place

    def _try_plus_one(self) -> None:
        logging.info(f"Usable plus ones: {self.board.usable_plus_ones}")
        while self.board.usable_plus_ones > 0:
            if not any(die.value is not None for die in self.dice_by_color.values()):
                logging.info("No dice with values available for plus one")
                break

            if self.automatic:
                should_use = random.choice([True, False])
            else:
                should_use = input('Use a plus one? (y/n): ').lower() == 'y'

            if not should_use:
                logging.info("Chose not to use plus one")
                break

            logging.info(f"Using plus one (remaining after use: {self.board.usable_plus_ones - 1})")
            picked = PlusOneAction().use(
                self.board, self.automatic,
                dice_by_color=self.dice_by_color,
            )
            if picked is None:
                logging.info("No die was picked for plus one")
                break

            actions = self._get_actions(picked, [])
            logging.info(f"Plus one actions: {actions}")
            self.action_handler.execute(actions, self.automatic)

    def execute(self) -> None:
        for game_round in range(1, self._NUM_ROUNDS + 1):
            logging.info("-" * 100)
            logging.info(f"Starting round {game_round}")

            self._try_reuse()
            self.roll_dice()
            self._try_reroll()

            if not self.available_dice:
                logging.info("No available dice left, ending round")
                break

            result = self.pick_die()
            if result is None:
                logging.info("No dice could be picked, ending round")
                break

            picked, smaller = result
            if not self._ask_to_place_die(picked):
                logging.info(f"Declined to place die {picked}, skipping placement")
                continue

            actions = self._get_actions(picked, smaller)
            self.action_handler.execute(actions, self.automatic)

            logging.info(f"Actions received in round {game_round}: {actions}")

            if not self.available_dice:
                logging.info("No available dice left, ending round")
                break

        self._try_plus_one()
