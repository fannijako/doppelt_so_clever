from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.dice.dice import Dice
from src.board.board import Board
from src.dice.dice_color import DiceColor
from src.logging_config import GameLogger
from src.actions.base_action import Action
from src.actions.action_handler import ActionHandler
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction

if TYPE_CHECKING:
    from src.input_handler import InputHandler

logger = GameLogger(__name__)


class ActiveRound:
    _NUM_ROUNDS = 3

    def __init__(
        self,
        board: Board,
        action_handler: ActionHandler,
        input_handler: InputHandler,
    ):
        self.board = board
        self.input_handler = input_handler
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
        self._log_state()

    def _log_state(self) -> None:
        logger.info("Available", ", ".join(str(die) for die in self.available_dice))
        logger.info("Picked", ", ".join(str(die) for die in self.picked_dice))
        logger.info("Discarded", ", ".join(str(die) for die in self.discarded_dice))

    def _pick_color(self) -> str:
        colors = [str(die.color.value) for die in self.available_dice]
        logger.info("Available colors", ", ".join(colors))

        color = self.input_handler.choose_value('Pick an available color: ', colors)
        logger.info("Picked color", color)
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

        logger.info("Picked die", picked)
        self._log_state()
        return picked, smaller

    def _get_actions(self, picked: Dice, smaller: list[Dice]) -> list[Action]:
        dispatch = {
            DiceColor.BLUE: lambda: self.board.blue_board_part.add_dice(
                picked, self.dice_by_color[DiceColor.WHITE]
            ),
            DiceColor.PINK: lambda: self.board.pink_board_part.add_dice(picked),
            DiceColor.GREEN: lambda: self.board.green_board_part.add_dice(picked),
            DiceColor.GREY: lambda: self.board.grey_board_part.place_dice(picked, self.input_handler, smaller),
            DiceColor.YELLOW: lambda: self.board.yellow_board_part.place_dice(picked, self.input_handler),
            DiceColor.WHITE: lambda: self.board.place_white_dice(picked, self.input_handler, self.dice_by_color, smaller),
        }
        handler = dispatch.get(picked.color)
        if not handler:
            return []
        result = handler()
        return result if isinstance(result, list) else [result] if result else []

    def _try_reuse(self) -> None:
        logger.info("Usable reuses", self.board.usable_reuses, f"discarded dice: {len(self.discarded_dice)}")
        while self.board.usable_reuses > 0 and self.discarded_dice:
            if not self.input_handler.confirm('Use a reuse? (y/n): '):
                logger.info("Reuse", "declined")
                break

            chosen_die = ReUseAction().use(
                self.board, self.input_handler,
                discarded_dice=self.discarded_dice,
            )
            if chosen_die is not None:
                self.discarded_dice.remove(chosen_die)
                self.available_dice.append(chosen_die)
                logger.info("Moved die", chosen_die, "discarded to available")

    def _try_reroll(self) -> None:
        logger.info("Usable rerolls", self.board.usable_rerolls)
        while self.board.usable_rerolls > 0:
            if not self.input_handler.confirm('Use a reroll? (y/n): '):
                logger.info("Reroll", "declined")
                break

            logger.info("Using reroll", f"remaining: {self.board.usable_rerolls - 1}")
            ReRollAction().use(self.board, self.input_handler)
            self.roll_dice()

    def _ask_to_place_die(self, picked: Dice) -> bool:
        should_place = self.input_handler.confirm(f'Place die {picked}? (y/n): ')
        logger.info("Place die", picked, "placed" if should_place else "skipped")
        return should_place

    def _try_plus_one(self) -> None:
        logger.info("Usable plus ones", self.board.usable_plus_ones)
        while self.board.usable_plus_ones > 0:
            if not any(die.value is not None for die in self.dice_by_color.values()):
                logger.info("Plus one", "no dice with values")
                break

            if not self.input_handler.confirm('Use a plus one? (y/n): '):
                logger.info("Plus one", "declined")
                break

            logger.info("Using plus one", f"remaining: {self.board.usable_plus_ones - 1}")
            picked = PlusOneAction().use(
                self.board, self.input_handler,
                dice_by_color=self.dice_by_color,
            )
            if picked is None:
                logger.info("Plus one", "no die picked")
                break

            actions = self._get_actions(picked, [])
            logger.info("Plus one actions", actions)
            self.action_handler.execute(actions, self.input_handler)

    def execute(self) -> None:
        for game_round in range(1, self._NUM_ROUNDS + 1):
            logger.info("Subround", game_round, "started")

            self._try_reuse()
            self.roll_dice()
            self._try_reroll()

            if not self.available_dice:
                logger.info("Status", "no available dice")
                logger.info("Subround", game_round, "completed")
                break

            result = self.pick_die()
            if result is None:
                logger.info("Status", "no dice could be picked")
                logger.info("Subround", game_round, "completed")
                break

            picked, smaller = result
            if not self._ask_to_place_die(picked):
                logger.info("Place die", picked, "declined")
                logger.info("Subround", game_round, "completed")
                continue

            actions = self._get_actions(picked, smaller)
            self.action_handler.execute(actions, self.input_handler)

            logger.info("Actions received", actions)

        self._try_plus_one()
