from __future__ import annotations

from typing import TYPE_CHECKING

from src.board.board import Board
from src.logging_config import GameLogger
from src.round.active_round import ActiveRound
from src.game.game_observer import GameObserver
from src.actions.action_source import ActionSource
from src.round.passive_round import PassiveRound
from src.actions.action_handler import ActionHandler
from src.ui.user_quit_exception import UserQuitException
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction
from src.actions.immediate_actions.black_question_mark import BlackQuestionMarkAction

if TYPE_CHECKING:
    from src.input_handler import InputHandler

logger = GameLogger(__name__)


class Game:  # pylint: disable=too-few-public-methods
    _NUMBER_OF_ROUNDS = 6
    _ROUND_ACTIONS = [
        ReRollAction,
        ReUseAction,
        PlusOneAction,
        BlackQuestionMarkAction,
        None,
        None,
    ]

    def __init__(
        self,
        input_handler: InputHandler,
        board: Board,
        observer: GameObserver,
        action_handler: ActionHandler,
    ):
        self.input_handler = input_handler
        self.board = board
        self.action_handler = action_handler
        self.observer = observer

    def play(self) -> int:
        try:
            for round_number in range(1, self._NUMBER_OF_ROUNDS + 1):
                self._play_round(round_number=round_number)
            score = self.board.evaluate()
            self.observer.on_game_ended(score)
            return score
        except UserQuitException:
            logger.info("Game quit by user")
            return -1
        finally:
            self.observer.close()

    def _play_round(self, round_number: int) -> None:
        self.observer.on_round_started(round_number)
        self._round_starting_action(round_number)
        self.observer.on_active_round_started()
        ActiveRound(self.board, self.action_handler, input_handler=self.input_handler, observer=self.observer).execute()
        logger.info("Round", round_number, "completed")

        logger.info("Passive round", round_number, "started")
        self.observer.on_passive_round_started()
        PassiveRound(self.board, self.action_handler, input_handler=self.input_handler, observer=self.observer).execute()
        logger.info("Passive round", round_number, "completed")
        self.observer.on_round_completed(round_number)

    def _round_starting_action(self, round_number: int) -> None:
        action = self._ROUND_ACTIONS[round_number - 1]
        if action is not None:
            action = action()
            logger.info("Action received", action.action_type.value, "round starting action")
            if action.is_immediate:
                self.action_handler.execute([action], input_handler=self.input_handler)
            else:
                new_action = action.save(board=self.board)
                if new_action:
                    self.action_handler.execute([new_action], input_handler=self.input_handler)
            self.observer.on_action_executed(ActionSource.ROUND_START, [action])
