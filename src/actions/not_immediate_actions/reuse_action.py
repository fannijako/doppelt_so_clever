from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.dice.dice import Dice
from src.logging_config import GameLogger
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.immediate_actions.pink_question_mark import PinkQuestionMarkAction
from src.actions.not_immediate_actions.not_immediate_actions import NotImmediateActions

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler

logger = GameLogger(__name__)


class ReUseAction(NotImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.REUSE)

    def save(self, board: Board) -> Optional[Action]:
        board.gained_reuses += 1
        board.usable_reuses += 1
        if board.gained_reuses == 6:
            return PinkQuestionMarkAction()
        return None

    def use(
        self,
        board: Board,
        input_handler: InputHandler,
        discarded_dice: list[Dice] = None,
    ) -> Optional[Dice]:
        if board.usable_reuses == 0:
            raise ValueError("No usable reuses")
        board.usable_reuses -= 1

        if discarded_dice is not None:
            index = input_handler.choose_index('Pick a discarded die index: ', discarded_dice)
            chosen_die = discarded_dice[index]

            logger.info("Reused die", chosen_die)
            return chosen_die

        return None
