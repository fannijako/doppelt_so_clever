from src.round.active_round import ActiveRound
from src.logging_config import GameLogger

logger = GameLogger(__name__)
from src.round.passive_round import PassiveRound
from src.board.board import Board
from src.actions.action_handler import ActionHandler
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction
from src.actions.immediate_actions.black_question_mark import BlackQuestionMarkAction


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

    def __init__(self, automatic: bool = True):
        self.automatic = automatic
        self.board = Board()
        self.action_handler = ActionHandler(board=self.board)

    def play(self) -> int:
        for round in range(1, self._NUMBER_OF_ROUNDS + 1):
            self._play_round(round=round)
        return self.board.evaluate()

    def _play_round(self, round: int) -> None:
        logger.info("Round", round, "started")
        self._round_starting_action(round)
        ActiveRound(self.board, self.action_handler, automatic=self.automatic).execute()
        logger.info("Round", round, "completed")

        logger.info("Passive round", round, "started")
        PassiveRound(self.board, self.action_handler, automatic=self.automatic).execute()
        logger.info("Passive round", round, "completed")

    def _round_starting_action(self, round: int) -> None:
        action = self._ROUND_ACTIONS[round - 1]
        if action is not None:
            action = action()
            logger.info("Action received", action.action_type.value, "round starting action")
            if action.is_immediate:
                self.action_handler.execute([action], automatic=self.automatic)
            else:
                new_action = action.save(board=self.board)
                if new_action:
                    self.action_handler.execute([new_action], automatic=self.automatic)
