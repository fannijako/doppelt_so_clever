from src.actions.action_handler import ActionHandler
from src.actions.immediate_actions.black_question_mark import BlackQuestionMarkAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.board.board import Board
from src.logging_config import GameLogger
from src.round.active_round import ActiveRound
from src.round.passive_round import PassiveRound

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

    def __init__(self, automatic: bool = True):
        self.automatic = automatic
        self.board = Board()
        self.action_handler = ActionHandler(board=self.board)

    def play(self) -> int:
        for round_number in range(1, self._NUMBER_OF_ROUNDS + 1):
            self._play_round(round_number=round_number)
        return self.board.evaluate()

    def _play_round(self, round_number: int) -> None:
        logger.info("Round", round_number, "started")
        self._round_starting_action(round_number)
        ActiveRound(self.board, self.action_handler, automatic=self.automatic).execute()
        logger.info("Round", round_number, "completed")

        logger.info("Passive round", round_number, "started")
        PassiveRound(self.board, self.action_handler, automatic=self.automatic).execute()
        logger.info("Passive round", round_number, "completed")

    def _round_starting_action(self, round_number: int) -> None:
        action = self._ROUND_ACTIONS[round_number - 1]
        if action is not None:
            action = action()
            logger.info("Action received", action.action_type.value, "round starting action")
            if action.is_immediate:
                self.action_handler.execute([action], automatic=self.automatic)
            else:
                new_action = action.save(board=self.board)
                if new_action:
                    self.action_handler.execute([new_action], automatic=self.automatic)
