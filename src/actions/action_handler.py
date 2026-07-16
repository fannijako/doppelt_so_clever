from __future__ import annotations

from typing import TYPE_CHECKING

from src.logging_config import GameLogger
from src.actions.base_action import Action
from src.actions.action_type import ActionType

if TYPE_CHECKING:
    from src.board.board import Board
    from src.input_handler import InputHandler

logger = GameLogger(__name__)


class ActionHandler:  # pylint: disable=too-few-public-methods
    def __init__(self, board: Board) -> list[Action]:
        self.board = board

    def execute(self, actions: list[Action], input_handler: InputHandler) -> None:
        not_used_immediate_actions = self._get_immediate_actions(actions)
        self._save_actions(self._get_not_immediate_actions(actions), not_used_immediate_actions)

        while not_used_immediate_actions:
            self.board.consumed_immediate_actions += 1
            logger.info("Executing", not_used_immediate_actions)

            action_index_to_use = self._pick_action_index_to_use(
                not_used_immediate_actions,
                input_handler=input_handler,
            )
            action_to_use = not_used_immediate_actions[action_index_to_use]
            logger.info("Action to use", action_to_use)

            actions_received = action_to_use.use(board=self.board, input_handler=input_handler)
            immediate_actions_received = self._get_immediate_actions(actions_received)
            not_immediate_actions_received = self._get_not_immediate_actions(actions_received)
            logger.info(
                "Actions received", actions_received,
                f"immediate: {immediate_actions_received}, not immediate: {not_immediate_actions_received}",
            )

            del not_used_immediate_actions[action_index_to_use]
            logger.info("Action list", "used action removed")

            not_used_immediate_actions.extend(immediate_actions_received)
            self._save_actions(not_immediate_actions_received, not_used_immediate_actions)

    def _save_actions(self, actions_to_save: list[Action], not_used_immediate_actions: list[Action]) -> None:
        for action in actions_to_save:
            chained_action = action.save(board=self.board)
            if chained_action is None:
                continue
            if chained_action.is_immediate:
                not_used_immediate_actions.append(chained_action)
            else:
                self._save_actions([chained_action], not_used_immediate_actions)

    def _pick_action_index_to_use(
        self,
        not_used_immediate_actions: list[Action],
        input_handler: InputHandler,
    ) -> int:
        return input_handler.choose_index('Add the index of the action to use: ', not_used_immediate_actions)

    def _get_number_of_actions_by_type(self, actions: list[Action], action_type: ActionType) -> int:
        return len([action for action in actions if action.action_type == action_type])

    def _get_immediate_actions(self, actions: list[Action]) -> list[Action]:
        return [action for action in actions if action.is_immediate]

    def _get_not_immediate_actions(self, actions: list[Action]) -> list[Action]:
        return [action for action in actions if not action.is_immediate]
