import logging

from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.board import Board


class ActionHandler:  # pylint: disable=too-few-public-methods
    def __init__(self, actions: list[Action], board: Board) -> list[Action]:
        self.actions = actions
        self.board = board
        self._not_immediate_actions_received = {
            ActionType.REROLL: self._get_number_of_actions_by_type(actions, ActionType.REROLL),
            ActionType.REUSE: self._get_number_of_actions_by_type(actions, ActionType.REUSE),
            ActionType.PLUS_ONE: self._get_number_of_actions_by_type(actions, ActionType.PLUS_ONE),
            ActionType.FOX: self._get_number_of_actions_by_type(actions, ActionType.FOX),
        }
        self._not_used_immediate_actions = self._get_immediate_actions(actions)

    def execute(self, automatic: bool = True) -> dict[ActionType, int]:

        while self._not_used_immediate_actions:
            logging.info(f'Executing ActionHandler with {self._not_used_immediate_actions=}')

            action_to_use = self._pick_action_to_use(automatic=automatic)
            logging.info(f'Action to use: {action_to_use}')

            actions_received = action_to_use.use(board=self.board)
            immediate_actions_received = self._get_immediate_actions(actions_received)
            not_immediate_actions_received = self._get_not_immediate_actions(actions_received)
            logging.info(
                f'Actions received: {actions_received}: '
                f'{immediate_actions_received=}, {not_immediate_actions_received=}'
            )

            if len(self._not_used_immediate_actions) > 1:
                self._not_used_immediate_actions = self._not_used_immediate_actions[1:]
            else:
                self._not_used_immediate_actions = []
            logging.info('Used action removed from action list')

            if immediate_actions_received:
                self._not_used_immediate_actions.extend(immediate_actions_received)
            if not_immediate_actions_received:
                for action in not_immediate_actions_received:
                    self._not_immediate_actions_received[action.action_type] += 1

        return self._not_immediate_actions_received

    def _pick_action_to_use(self, automatic: bool = True) -> Action:
        if automatic:
            return self._not_used_immediate_actions[0]
        while True:
            try:
                return self._not_used_immediate_actions[int(input('Add the index of the action to use: '))]
            except ValueError:
                logging.error('Invalid index')

    def _get_number_of_actions_by_type(self, actions: list[Action], action_type: ActionType) -> int:
        return len([action for action in actions if action.action_type == action_type])

    def _get_immediate_actions(self, actions: list[Action]) -> list[Action]:
        return [action for action in actions if action.is_immediate]

    def _get_not_immediate_actions(self, actions: list[Action]) -> list[Action]:
        return [action for action in actions if not action.is_immediate]
