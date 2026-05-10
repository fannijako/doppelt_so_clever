from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler


def _fake_policy(_state, _action_mask):
    return 0, -0.5, 1.0


def _make_handler():
    board = Board()
    observer = RLObserver(board)
    handler = RLInputHandler(observer, _fake_policy, training=True)
    return handler


class TestTrajectoryRecording:
    def test_trajectory_empty_initially(self):
        handler = _make_handler()
        assert not handler.trajectory

    def test_trajectory_grows_on_decision(self):
        handler = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        assert len(handler.trajectory) == 1

    def test_transition_has_no_reward_field(self):
        handler = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        assert not hasattr(handler.trajectory[0], "reward")
