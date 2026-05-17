from typing import Any

from src.actions.action_handler import ActionHandler
from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.board.board import Board
from src.input_handler.base_input_handler import InputHandler


class RecordingImmediateAction(Action):
    def __init__(self, label: str, calls: list[str]):
        super().__init__(action_type=ActionType.NONE, is_immediate=True)
        self.label = label
        self.calls = calls

    def save(self, board: Board) -> Action:
        raise ValueError("Action cannot be saved")

    def use(self, board: Board, input_handler: InputHandler) -> list[Action]:
        self.calls.append(self.label)
        return []


class IndexedInputHandler(InputHandler):
    def __init__(self, first_index: int):
        self.first_index = first_index
        self.calls = 0

    def choose_index(self, prompt: str, options: list[Any]) -> int:
        if self.calls == 0:
            self.calls += 1
            return self.first_index
        self.calls += 1
        return 0

    def confirm(self, prompt: str) -> bool:
        raise NotImplementedError

    def choose_value(self, prompt: str, valid_values: list[str]) -> str:
        raise NotImplementedError


def _make_actions(calls: list[str]) -> list[Action]:
    return [
        RecordingImmediateAction("first", calls),
        RecordingImmediateAction("middle", calls),
        RecordingImmediateAction("last", calls),
    ]


class TestActionHandlerSelectedActionRemoval:
    def test_executes_selected_first_action(self):
        calls: list[str] = []
        ActionHandler(Board()).execute(_make_actions(calls), IndexedInputHandler(0))
        assert calls[0] == "first"

    def test_executes_selected_middle_action(self):
        calls: list[str] = []
        ActionHandler(Board()).execute(_make_actions(calls), IndexedInputHandler(1))
        assert calls[0] == "middle"

    def test_executes_selected_last_action(self):
        calls: list[str] = []
        ActionHandler(Board()).execute(_make_actions(calls), IndexedInputHandler(2))
        assert calls[0] == "last"


class TestActionHandlerConsumedImmediateCount:  # pylint: disable=too-few-public-methods
    def test_counts_each_immediate_action_consumed(self):
        board = Board()
        ActionHandler(board).execute(_make_actions([]), IndexedInputHandler(0))
        assert board.consumed_immediate_actions == 3
