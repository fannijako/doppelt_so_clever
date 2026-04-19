"""Pygame-based game wrapper for Doppelt So Clever."""

import logging
from typing import Any

import pygame

from src.game import Game
from src.ui.pygame_ui import PygameUI
from src.board.board import Board
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.round.active_round import ActiveRound
from src.round.passive_round import PassiveRound
from src.actions.action_handler import ActionHandler
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction


class PygameGame(Game):
    """Game subclass that uses Pygame UI for input."""

    def __init__(self):  # pylint: disable=super-init-not-called
        # Don't call super().__init__ since we handle our own setup
        self.automatic = False
        self.board = Board()
        self.action_handler = ActionHandler(board=self.board)
        self.ui = PygameUI(self.board)

        # Monkey-patch input methods
        self._patch_board()
        self._patch_rounds()
        self._patch_actions()

    def _patch_board(self) -> None:
        """Patch Board methods to use UI."""
        def patched_place_white(white_dice, automatic, dice_by_color, smaller_die=None):  # pylint: disable=unused-argument
            if smaller_die is None:
                smaller_die = []

            self.ui.update_dice(list(dice_by_color.values()))
            self.ui.refresh()

            available = [DiceColor.BLUE, DiceColor.GREEN, DiceColor.PINK, DiceColor.YELLOW, DiceColor.GREY]
            colors = list(available)

            self.ui.show_message(f"White dice rolled {white_dice.value}. Pick a color to play as:")
            result = self.ui.wait_for_input("color_choice", colors, "Select color for white dice")

            play_as = DiceColor(result)

            if play_as == DiceColor.BLUE:
                return self.board.blue_board_part.add_dice(
                    dice_by_color[DiceColor.BLUE], white_dice
                )
            if play_as == DiceColor.GREEN:
                return self.board.green_board_part.add_dice(white_dice)
            if play_as == DiceColor.PINK:
                return self.board.pink_board_part.add_dice(white_dice)
            if play_as == DiceColor.YELLOW:
                return self._yellow_placement(white_dice)
            if play_as == DiceColor.GREY:
                return self._grey_placement(white_dice, smaller_die)

            return []

        self.board.place_white_dice = patched_place_white

    def _yellow_placement(self, dice: Dice) -> list:
        """Handle yellow board placement with UI."""
        from src.board.board_parts.yellow_board_part import YellowBoardAction  # pylint: disable=import-outside-toplevel

        placements = self.board.yellow_board_part.possible_dice_placements(dice)
        if not placements:
            return []

        if len(placements) == 1:
            placement = placements[0]
        else:
            options = [
                f"Row {p[0]}, Col {p[1]}, {'Circle' if p[2] == YellowBoardAction.CIRCLE else 'Cross'}"
                for p in placements
            ]
            self.ui.show_message("Select placement for yellow dice:")
            idx = self.ui.wait_for_input("action_index", options, "Pick placement")
            placement = placements[idx]

        return self.board.yellow_board_part.add_dice(
            dice=dice,
            row_position=placement[0],
            column_position=placement[1],
            action=placement[2]
        )

    def _grey_placement(self, dice: Dice, smaller_die: list) -> list:
        """Handle grey board placement with UI."""
        all_die = [dice] + smaller_die
        has_white = any(d.color == DiceColor.WHITE for d in all_die)
        has_grey = any(d.color == DiceColor.GREY for d in all_die)

        colors = [DiceColor.YELLOW, DiceColor.BLUE, DiceColor.PINK, DiceColor.GREEN]

        color_to_use_white_as = None
        if has_white:
            self.ui.show_message("Pick color to substitute WHITE as:")
            result = self.ui.wait_for_input("color_choice", colors, "Select color for white")
            color_to_use_white_as = DiceColor(result)

        color_to_use_grey_as = None
        if has_grey:
            self.ui.show_message("Pick color to substitute GREY as:")
            result = self.ui.wait_for_input("color_choice", colors, "Select color for grey")
            color_to_use_grey_as = DiceColor(result)

        return self.board.grey_board_part.add_dice(
            dice=dice,
            smaller_die=smaller_die,
            color_to_use_white_as=color_to_use_white_as,
            color_to_use_grey_as=color_to_use_grey_as
        )

    def _patch_rounds(self) -> None:
        """Patch round classes - we override execute methods instead."""

    def _patch_actions(self) -> None:
        """Patch action classes to use UI."""
        def patched_reuse_use(self_action, board, automatic, discarded_dice=None):  # pylint: disable=unused-argument
            if board.usable_reuses == 0:
                raise ValueError("No usable reuses")
            board.usable_reuses -= 1

            if discarded_dice:
                self.ui.show_message("Select a discarded die to reuse:")
                options = [str(d) for d in discarded_dice]
                idx = self.ui.wait_for_input("dice_index", options, "Pick discarded die")
                chosen = discarded_dice[idx]
                logging.info(f"Reused die: {chosen}")
                return chosen
            return None

        ReUseAction.use = patched_reuse_use

        def patched_plusone_use(self_action, board, automatic, dice_by_color=None):  # pylint: disable=unused-argument
            if board.usable_plus_ones == 0:
                raise ValueError("No usable plus ones")
            board.usable_plus_ones -= 1

            if dice_by_color:
                usable = [d for d in dice_by_color.values() if d.value is not None]
                if not usable:
                    return None

                self.ui.show_message("Select a die to use +1 on:")
                options = [d.color.value for d in usable]
                result = self.ui.wait_for_input("dice_color", options, "Pick die color")
                chosen = dice_by_color[DiceColor(result)]
                logging.info(f"Plus one used with die: {chosen}")
                return chosen
            return None

        PlusOneAction.use = patched_plusone_use

        def patched_reroll_use(self_action, board, automatic):  # pylint: disable=unused-argument
            if board.usable_rerolls == 0:
                raise ValueError("No usable rerolls")
            board.usable_rerolls -= 1
            logging.info(f"Used reroll, remaining: {board.usable_rerolls}")

        ReRollAction.use = patched_reroll_use

    def _ask_yes_no(self, message: str) -> bool:
        """Ask user a yes/no question via UI."""
        self.ui.show_message(message)
        return self.ui.wait_for_input("yes_no", [True, False], message)

    def _pick_from_options(self, message: str, options: list, display_func=None) -> Any:
        """Ask user to pick from options."""
        display_options = [display_func(o) if display_func else str(o) for o in options]
        self.ui.show_message(message)
        idx = self.ui.wait_for_input("action_index", display_options, message)
        return options[idx]

    def _apply_reuses(self, round_obj) -> None:
        """Offer reuse of discarded dice before rolling."""
        while self.board.usable_reuses > 0 and round_obj.discarded_dice:
            if self._ask_yes_no(f"Use a reuse? ({len(round_obj.discarded_dice)} discarded dice)"):
                options = [str(d) for d in round_obj.discarded_dice]
                idx = self.ui.wait_for_input("dice_index", options, "Pick die to reuse")
                chosen = round_obj.discarded_dice[idx]
                round_obj.discarded_dice.remove(chosen)
                round_obj.available_dice.append(chosen)
            else:
                break

    def _apply_rerolls(self, round_obj) -> None:
        """Offer rerolls after initial roll."""
        while self.board.usable_rerolls > 0:
            if self._ask_yes_no("Use a reroll?"):
                self.board.usable_rerolls -= 1
                for die in round_obj.available_dice:
                    die.roll()
                round_obj.roll_dice()
                self.ui.update_dice(round_obj.available_dice, round_obj.discarded_dice)
                self.ui.refresh()
            else:
                break

    def _pick_die(self, round_obj):
        """Ask user to pick a die; return the picked die or None."""
        self.ui.show_message("Select a die color:")
        options = [str(d.color.value) for d in round_obj.available_dice]
        result = self.ui.wait_for_input("dice_color", options, "Pick a die")
        for d in round_obj.available_dice:
            if str(d.color.value) == result:
                return d
        return None

    def _run_active_round(self, round_num: int) -> None:
        """Run an active round with UI."""
        round_obj = ActiveRound(self.board, self.action_handler, automatic=False)
        dice_by_color = round_obj.dice_by_color

        for game_round in range(1, 4):  # 3 sub-rounds
            logging.info(f"Active round {round_num}, sub-round {game_round}")

            self._apply_reuses(round_obj)

            # Roll dice
            for die in round_obj.available_dice:
                die.roll()
            round_obj.roll_dice()  # This logs
            self.ui.update_dice(round_obj.available_dice, round_obj.discarded_dice)
            self.ui.refresh()

            self._apply_rerolls(round_obj)

            if not round_obj.available_dice:
                break

            picked = self._pick_die(round_obj)
            if not picked:
                break

            # Calculate smaller dice
            smaller = [d for d in round_obj.available_dice if d.value < picked.value]
            round_obj.available_dice.remove(picked)
            for d in smaller:
                round_obj.available_dice.remove(d)
            round_obj.picked_dice.append(picked)
            round_obj.discarded_dice.extend(smaller)

            self.ui.update_dice(round_obj.available_dice, round_obj.discarded_dice)

            if not self._ask_yes_no(f"Place {picked}?"):
                continue

            actions = self._get_die_actions(picked, smaller, dice_by_color)
            self.action_handler.execute(actions, automatic=False)

            if not round_obj.available_dice:
                break

        # Try plus one at end
        self._try_plus_one(round_obj, dice_by_color)

    def _get_die_actions(self, picked: Dice, smaller: list, dice_by_color: dict):
        """Get actions for a picked die."""
        actions = []
        if picked.color == DiceColor.BLUE:
            action = self.board.blue_board_part.add_dice(picked, dice_by_color[DiceColor.WHITE])
            if action:
                actions = [action]
        elif picked.color == DiceColor.PINK:
            action = self.board.pink_board_part.add_dice(picked)
            if action:
                actions = [action]
        elif picked.color == DiceColor.GREEN:
            action = self.board.green_board_part.add_dice(picked)
            if action:
                actions = [action]
        elif picked.color == DiceColor.GREY:
            actions = self._grey_placement(picked, smaller)
        elif picked.color == DiceColor.YELLOW:
            actions = self._yellow_placement(picked)
        elif picked.color == DiceColor.WHITE:
            # Handle white via patched method
            actions = self.board.place_white_dice(picked, False, dice_by_color, smaller)

        # Filter out None values
        return [a for a in actions if a is not None]

    def _try_plus_one(self, round_obj, dice_by_color: dict) -> None:  # pylint: disable=unused-argument
        """Handle plus one actions."""
        while self.board.usable_plus_ones > 0:
            usable = [d for d in dice_by_color.values() if d.value is not None]
            if not usable:
                break

            if not self._ask_yes_no("Use a plus one?"):
                break

            self.ui.show_message("Select die for +1:")
            options = [d.color.value for d in usable]
            result = self.ui.wait_for_input("dice_color", options, "Pick die")
            picked = dice_by_color[DiceColor(result)]

            actions = self._get_die_actions(picked, [], dice_by_color)
            self.action_handler.execute(actions, automatic=False)

    def _run_passive_round(self) -> None:
        """Run a passive round with UI."""
        round_obj = PassiveRound(self.board, self.action_handler, automatic=False)
        dice_by_color = round_obj.dice_by_color

        # Roll all dice
        for die in dice_by_color.values():
            die.roll()

        all_dice = list(dice_by_color.values())
        eligible = round_obj._get_lowest_n_dice(all_dice, 3)  # pylint: disable=protected-access

        if not eligible:
            return

        self.ui.show_message("Passive turn: Pick one of the 3 lowest dice")
        options = [str(d) for d in eligible]
        idx = self.ui.wait_for_input("dice_index", options, "Pick a die")
        picked = eligible[idx]

        # Execute action based on picked color
        actions = self._get_passive_actions(picked, dice_by_color)
        self.action_handler.execute(actions, automatic=False)

    def _get_passive_actions(self, picked: Dice, dice_by_color: dict):
        """Get actions for passive round."""
        actions = []
        if picked.color == DiceColor.BLUE:
            action = self.board.blue_board_part.add_dice(picked, dice_by_color[DiceColor.WHITE])
            if action:
                actions = [action]
        elif picked.color == DiceColor.PINK:
            action = self.board.pink_board_part.add_dice(picked)
            if action:
                actions = [action]
        elif picked.color == DiceColor.GREEN:
            action = self.board.green_board_part.add_dice(picked)
            if action:
                actions = [action]
        elif picked.color == DiceColor.GREY:
            actions = self._grey_placement(picked, [])
        elif picked.color == DiceColor.YELLOW:
            actions = self._yellow_placement(picked)
        elif picked.color == DiceColor.WHITE:
            actions = self.board.place_white_dice(picked, False, dice_by_color, [])

        return [a for a in actions if a is not None]

    def play(self) -> int:
        """Main game loop with Pygame UI."""
        try:
            # Grant round actions (same as original)
            round_actions = [
                ReUseAction,
                ReUseAction,
                PlusOneAction,
                None,  # Black question mark - not implemented in original
            ]

            for active_round_num in range(1, 7):
                logging.info("=" * 50)
                logging.info(f"Starting active round {active_round_num}")

                # Grant automatic action if applicable
                if active_round_num - 1 < len(round_actions) and round_actions[active_round_num - 1]:
                    action = round_actions[active_round_num - 1]()
                    if action.is_immediate:
                        self.action_handler.execute([action], automatic=False)
                    else:
                        new_action = action.save(board=self.board)
                        if new_action:
                            self.action_handler.execute([new_action], automatic=False)

                # Run active round with UI
                self._run_active_round(active_round_num)

                # Run passive round with UI
                self._run_passive_round()

            # Final score
            score = self.board.evaluate()
            self.ui.show_message(f"Game Over! Final Score: {score}")

            # Wait for user to close
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        waiting = False
                    if event.type == pygame.KEYDOWN:
                        waiting = False
                self.ui.refresh()

            return score

        finally:
            self.ui.close()
