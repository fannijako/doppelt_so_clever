from typing import Any

from src.actions.action_handler import ActionHandler
from src.actions.action_type import ActionType
from src.actions.base_action import Action
from src.actions.not_immediate_actions.fox_action import FoxAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction
from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.reuse_action import ReUseAction
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


class YieldingImmediateAction(Action):
    def __init__(self, yields: list[Action]):
        super().__init__(action_type=ActionType.NONE, is_immediate=True)
        self.yields = yields

    def save(self, board: Board) -> Action:
        raise ValueError("Action cannot be saved")

    def use(self, board: Board, input_handler: InputHandler) -> list[Action]:
        return self.yields


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


class TestActionHandlerInitialNotImmediateActions:
    def test_saves_plus_one_from_initial_actions(self):
        board = Board()
        ActionHandler(board).execute([PlusOneAction()], IndexedInputHandler(0))
        assert board.usable_plus_ones == 1

    def test_saves_fox_from_initial_actions(self):
        board = Board()
        ActionHandler(board).execute([FoxAction()], IndexedInputHandler(0))
        assert board.foxes == 1

    def test_saves_plus_one_received_alongside_immediate_action(self):
        board = Board()
        ActionHandler(board).execute(
            [YieldingImmediateAction([]), PlusOneAction()],
            IndexedInputHandler(0),
        )
        assert board.usable_plus_ones == 1


class TestActionHandlerReceivedNotImmediateActions:
    def test_saves_reroll_received_from_used_action(self):
        board = Board()
        ActionHandler(board).execute([YieldingImmediateAction([ReRollAction()])], IndexedInputHandler(0))
        assert board.usable_rerolls == 1

    def test_saves_fox_when_sixth_reroll_is_received(self):
        board = Board()
        board.gained_rerolls = 5
        ActionHandler(board).execute([YieldingImmediateAction([ReRollAction()])], IndexedInputHandler(0))
        assert board.foxes == 1

    def test_executes_pink_question_mark_when_sixth_reuse_is_received(self):
        board = Board()
        board.gained_reuses = 5
        ActionHandler(board).execute([YieldingImmediateAction([ReUseAction()])], IndexedInputHandler(0))
        assert board.pink_board_part.boxes[0].value_used == 6
