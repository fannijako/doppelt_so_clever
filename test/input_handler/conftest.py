import pytest

from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler


class FakePolicy:  # pylint: disable=too-few-public-methods
    def __init__(self, action: int = 0, log_prob: float = -0.5, value: float = 1.0):
        self.action = action
        self.log_prob = log_prob
        self.value = value
        self.calls: list[tuple[list[float], list[bool]]] = []

    def __call__(
        self, state: list[float], action_mask: list[bool]
    ) -> tuple[int, float, float]:
        self.calls.append((state, action_mask))
        return self.action, self.log_prob, self.value


def _make_observer():
    return RLObserver(Board())


def _make_policy():
    return FakePolicy()


@pytest.fixture()
def handler():
    policy = _make_policy()
    return RLInputHandler(_make_observer(), policy), policy


@pytest.fixture()
def eval_handler():
    policy = _make_policy()
    return RLInputHandler(_make_observer(), policy, training=False), policy
