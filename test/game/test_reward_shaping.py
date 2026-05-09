from unittest.mock import patch

import pytest

from src.board.board import Board
from src.game.rl_observer import RLObserver


class TestRewardShapingDisabled:
    def test_no_reward_accumulated_without_flag(self):
        observer = RLObserver(Board(), reward_shaping=False)
        observer.on_board_updated()
        assert observer.get_step_reward() == 0.0

    def test_step_reward_zero_initially(self):
        observer = RLObserver(Board(), reward_shaping=True)
        assert observer.get_step_reward() == 0.0


class TestRewardShapingEnabled:
    def test_accumulates_delta_on_board_updated(self):
        board = Board()
        observer = RLObserver(board, reward_shaping=True)
        with patch.object(board, "evaluate", return_value=10):
            observer.on_board_updated()
        assert observer.get_step_reward() == 10.0

    def test_resets_after_get(self):
        board = Board()
        observer = RLObserver(board, reward_shaping=True)
        with patch.object(board, "evaluate", return_value=5):
            observer.on_board_updated()
        observer.get_step_reward()
        assert observer.get_step_reward() == 0.0

    def test_accumulates_multiple_updates(self):
        board = Board()
        observer = RLObserver(board, reward_shaping=True)
        scores = [10, 25]
        with patch.object(board, "evaluate", side_effect=scores):
            observer.on_board_updated()
            observer.on_board_updated()
        assert observer.get_step_reward() == pytest.approx(25.0)

    def test_tracks_prev_score_correctly(self):
        board = Board()
        observer = RLObserver(board, reward_shaping=True)
        with patch.object(board, "evaluate", return_value=10):
            observer.on_board_updated()
        observer.get_step_reward()
        with patch.object(board, "evaluate", return_value=18):
            observer.on_board_updated()
        assert observer.get_step_reward() == pytest.approx(8.0)
