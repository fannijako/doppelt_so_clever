import logging

from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.board import Board


class ActionHandler:  # pylint: disable=too-few-public-methods
    def __init__(self, board: Board) -> list[Action]:
        self.board = board

    def execute(self, actions: list[Action], automatic: bool = True) -> None:
        not_used_immediate_actions = self._get_immediate_actions(actions)

        while not_used_immediate_actions:
            logging.info(f'Executing ActionHandler with {not_used_immediate_actions=}')

            action_to_use = self._pick_action_to_use(not_used_immediate_actions, automatic=automatic)
            logging.info(f'Action to use: {action_to_use}')

            actions_received = action_to_use.use(board=self.board, automatic=automatic)
            immediate_actions_received = self._get_immediate_actions(actions_received)
            not_immediate_actions_received = self._get_not_immediate_actions(actions_received)
            logging.info(
                f'Actions received: {actions_received}: '
                f'{immediate_actions_received=}, {not_immediate_actions_received=}'
            )

            if len(not_used_immediate_actions) > 1:
                not_used_immediate_actions = not_used_immediate_actions[1:]
            else:
                not_used_immediate_actions = []
            logging.info('Used action removed from action list')

            if immediate_actions_received:
                not_used_immediate_actions.extend(immediate_actions_received)
            if not_immediate_actions_received:
                for action in not_immediate_actions_received:
                    new_action = action.save(board=self.board)
                    if new_action:
                        not_used_immediate_actions.append(new_action)

    def _pick_action_to_use(self, not_used_immediate_actions: list[Action], automatic: bool = True) -> Action:
        if automatic:
            return not_used_immediate_actions[0]
        while True:
            try:
                return not_used_immediate_actions[int(input('Add the index of the action to use: '))]
            except ValueError:
                logging.error('Invalid index')

    def _get_number_of_actions_by_type(self, actions: list[Action], action_type: ActionType) -> int:
        return len([action for action in actions if action.action_type == action_type])

    def _get_immediate_actions(self, actions: list[Action]) -> list[Action]:
        return [action for action in actions if action.is_immediate]

    def _get_not_immediate_actions(self, actions: list[Action]) -> list[Action]:
        return [action for action in actions if not action.is_immediate]
