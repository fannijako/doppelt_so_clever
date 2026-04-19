import logging
from typing import Any

import pygame

from src.game import Game
from src.ui.pygame_ui import PygameUI
from src.board.board_parts.yellow_board_part import YellowBoardAction
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.round.active_round import ActiveRound
from src.round.passive_round import PassiveRound
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction


class PygameGame(Game):
    def __init__(self):
        super().__init__(automatic=False)
        self.ui = PygameUI(self.board)

    def _white_placement(self, dice: Dice, dice_by_color: dict, smaller_die: list) -> list:
        colors = [DiceColor.BLUE, DiceColor.GREEN, DiceColor.PINK, DiceColor.YELLOW, DiceColor.GREY]

        self.ui.show_message(f"White dice rolled {dice.value}. Pick a color to play as:")
        result = self.ui.wait_for_input("color_choice", colors, "Select color for white dice")
        play_as = DiceColor(result)

        dispatch = {
            DiceColor.BLUE: lambda: self.board.blue_board_part.add_dice(dice_by_color[DiceColor.BLUE], dice),
            DiceColor.GREEN: lambda: self.board.green_board_part.add_dice(dice),
            DiceColor.PINK: lambda: self.board.pink_board_part.add_dice(dice),
            DiceColor.YELLOW: lambda: self._yellow_placement(dice),
            DiceColor.GREY: lambda: self._grey_placement(dice, smaller_die),
        }
        result = dispatch[play_as]()
        return result if isinstance(result, list) else [result] if result else []

    def _yellow_placement(self, dice: Dice) -> list:
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

    def _ask_yes_no(self, message: str) -> bool:
        self.ui.show_message(message)
        return self.ui.wait_for_input("yes_no", [True, False], message)

    def _pick_from_options(self, message: str, options: list, display_func=None) -> Any:
        display_options = [display_func(o) if display_func else str(o) for o in options]
        self.ui.show_message(message)
        idx = self.ui.wait_for_input("action_index", display_options, message)
        return options[idx]

    def _apply_reuses(self, round_obj) -> None:
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
        self.ui.show_message("Select a die color:")
        options = [str(d.color.value) for d in round_obj.available_dice]
        result = self.ui.wait_for_input("dice_color", options, "Pick a die")
        for d in round_obj.available_dice:
            if str(d.color.value) == result:
                return d
        return None

    def _run_active_round(self, round_num: int) -> None:
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

            smaller = [d for d in round_obj.available_dice if d.value < picked.value]
            round_obj.available_dice.remove(picked)
            for d in smaller:
                round_obj.available_dice.remove(d)
            round_obj.picked_dice.append(picked)
            round_obj.discarded_dice.extend(smaller)

            self.ui.update_dice(round_obj.available_dice, round_obj.discarded_dice)

            if not self._ask_yes_no(f"Place {picked}?"):
                continue

            actions = self._get_placement_actions(picked, dice_by_color, smaller)
            self.action_handler.execute(actions, automatic=False)

            if not round_obj.available_dice:
                break

        self._try_plus_one(None, dice_by_color)

    def _get_placement_actions(self, picked: Dice, dice_by_color: dict, smaller: list = None) -> list:
        if smaller is None:
            smaller = []

        dispatch = {
            DiceColor.BLUE: lambda: self.board.blue_board_part.add_dice(picked, dice_by_color[DiceColor.WHITE]),
            DiceColor.PINK: lambda: self.board.pink_board_part.add_dice(picked),
            DiceColor.GREEN: lambda: self.board.green_board_part.add_dice(picked),
            DiceColor.GREY: lambda: self._grey_placement(picked, smaller),
            DiceColor.YELLOW: lambda: self._yellow_placement(picked),
            DiceColor.WHITE: lambda: self._white_placement(picked, dice_by_color, smaller),
        }

        handler = dispatch.get(picked.color)
        if not handler:
            return []
        result = handler()
        return [a for a in (result if isinstance(result, list) else [result]) if a is not None]

    def _try_plus_one(self, _, dice_by_color: dict) -> None:
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

            actions = self._get_placement_actions(picked, dice_by_color)
            self.action_handler.execute(actions, automatic=False)

    def _run_passive_round(self) -> None:
        round_obj = PassiveRound(self.board, self.action_handler, automatic=False)
        dice_by_color = round_obj.dice_by_color

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

        actions = self._get_placement_actions(picked, dice_by_color)
        self.action_handler.execute(actions, automatic=False)

    def play(self) -> int:
        try:
            round_actions = [
                ReUseAction,
                ReUseAction,
                PlusOneAction,
                None,  # Black question mark - not implemented in original
            ]

            for active_round_num in range(1, 7):
                logging.info("=" * 50)
                logging.info(f"Starting active round {active_round_num}")

                if active_round_num - 1 < len(round_actions) and round_actions[active_round_num - 1]:
                    action = round_actions[active_round_num - 1]()
                    if action.is_immediate:
                        self.action_handler.execute([action], automatic=False)
                    else:
                        new_action = action.save(board=self.board)
                        if new_action:
                            self.action_handler.execute([new_action], automatic=False)

                self._run_active_round(active_round_num)

                self._run_passive_round()

            score = self.board.evaluate()
            self.ui.show_message(f"Game Over! Final Score: {score}")

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
