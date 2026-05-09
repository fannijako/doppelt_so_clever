from unittest.mock import patch

from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler


def _fake_policy(_state, _action_mask):
    return 0, -0.5, 1.0


def _make_handler(reward_shaping=False):
    board = Board()
    observer = RLObserver(board, reward_shaping=reward_shaping)
    handler = RLInputHandler(observer, _fake_policy, training=True)
    return handler, observer, board


class TestFlushFinalReward:
    def test_flush_with_empty_trajectory_no_error(self):
        handler, _, _ = _make_handler()
        handler.flush_final_reward()

    def test_flush_assigns_accumulated_reward(self):
        handler, observer, board = _make_handler(reward_shaping=True)
        handler.choose_index("pick", ["a", "b"])
        with patch.object(board, "evaluate", return_value=15):
            observer.on_board_updated()
        handler.flush_final_reward()
        assert handler.trajectory[-1].reward == 15.0


class TestStepRewardPropagation:
    def test_reward_assigned_to_previous_transition(self):
        handler, observer, board = _make_handler(reward_shaping=True)
        handler.choose_index("pick", ["a"])
        with patch.object(board, "evaluate", return_value=10):
            observer.on_board_updated()
        handler.choose_index("pick", ["a"])
        assert handler.trajectory[0].reward == 10.0

    def test_second_transition_starts_with_zero_reward(self):
        handler, observer, board = _make_handler(reward_shaping=True)
        handler.choose_index("pick", ["a"])
        with patch.object(board, "evaluate", return_value=10):
            observer.on_board_updated()
        handler.choose_index("pick", ["a"])
        assert handler.trajectory[1].reward == 0.0

    def test_no_reward_without_shaping(self):
        handler, observer, board = _make_handler(reward_shaping=False)
        handler.choose_index("pick", ["a"])
        with patch.object(board, "evaluate", return_value=99):
            observer.on_board_updated()
        handler.choose_index("pick", ["a"])
        assert handler.trajectory[0].reward == 0.0
