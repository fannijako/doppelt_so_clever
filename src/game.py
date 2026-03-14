import logging

from src.round.active_round import ActiveRound
from src.board.board import Board
from src.actions.action_handler import ActionHandler
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction
from src.actions.immediate_actions.black_question_mark import BlackQuestionMarkAction


class Game:  # pylint: disable=too-few-public-methods
    _NUM_ACTIVE_ROUNDS = 6
    _ROUND_ACTIONS = [
        ReRollAction,
        ReUseAction,
        PlusOneAction,
        BlackQuestionMarkAction,
    ]

    def __init__(self, automatic: bool = True):
        self.automatic = automatic
        self.board = Board()
        self.action_handler = ActionHandler(board=self.board)

    def play(self) -> int:
        for active_round_number in range(1, self._NUM_ACTIVE_ROUNDS + 1):
            logging.info("=" * 100)
            logging.info(f"Starting active round {active_round_number}")

            if active_round_number <= len(self._ROUND_ACTIONS):
                action = self._ROUND_ACTIONS[active_round_number - 1]()
                logging.info(f"Granting automatic action: {action.action_type.value}")
                if action.is_immediate:
                    self.action_handler.execute([action], automatic=self.automatic)
                else:
                    new_action = action.save(board=self.board)
                    if new_action:
                        self.action_handler.execute([new_action], automatic=self.automatic)

            active_round = ActiveRound(self.board, self.action_handler, automatic=self.automatic)
            active_round.execute()

        score = self.board.evaluate()
        logging.info(f"board value: {score}")
        return score
