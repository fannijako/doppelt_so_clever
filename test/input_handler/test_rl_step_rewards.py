from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler


def _fake_policy(_state, _action_mask):
    return 0, -0.5, 1.0


def _make_handler():
    board = Board()
    observer = RLObserver(board)
    handler = RLInputHandler(observer, _fake_policy, training=True)
    return handler, board, observer


class TestTrajectoryRecording:
    def test_trajectory_empty_initially(self):
        handler, _board, _observer = _make_handler()
        assert not handler.trajectory

    def test_trajectory_grows_on_decision(self):
        handler, _board, _observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        assert len(handler.trajectory) == 1

    def test_transition_has_reward_field_initialized_zero(self):
        handler, _board, _observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        assert handler.trajectory[0].reward == 0.0


class TestStepRewardAttribution:
    def test_unchanged_board_yields_zero_reward(self):
        handler, _board, _observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        handler.choose_index("pick", ["a", "b"])
        assert handler.trajectory[0].reward == 0.0

    def test_failed_action_penalty_lands_on_previous_transition(self):
        handler, _board, observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        observer.on_action_executed(source=None, actions=[])
        handler.choose_index("pick", ["a", "b"])
        assert handler.trajectory[0].reward < 0.0

    def test_fox_gain_rewards_previous_transition(self):
        handler, board, _observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        board.foxes += 1
        handler.choose_index("pick", ["a", "b"])
        assert handler.trajectory[0].reward > 0.0

    def test_resource_gain_rewards_previous_transition(self):
        handler, board, _observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        board.gained_rerolls += 1
        handler.choose_index("pick", ["a", "b"])
        assert handler.trajectory[0].reward > 0.0

    def test_flush_writes_tail_delta_to_last_transition(self):
        handler, board, _observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        board.foxes += 1
        handler.flush_terminal_step_reward()
        assert handler.trajectory[0].reward > 0.0

    def test_flush_is_noop_when_no_delta(self):
        handler, _board, _observer = _make_handler()
        handler.choose_index("pick", ["a", "b"])
        handler.flush_terminal_step_reward()
        assert handler.trajectory[0].reward == 0.0


class TestEvalModeNoShaping:
    def test_eval_handler_does_not_record_transitions(self):
        board = Board()
        observer = RLObserver(board)
        handler = RLInputHandler(observer, _fake_policy, training=False)
        handler.choose_index("pick", ["a", "b"])
        assert not handler.trajectory

    def test_eval_handler_flush_is_safe(self):
        board = Board()
        observer = RLObserver(board)
        handler = RLInputHandler(observer, _fake_policy, training=False)
        handler.choose_index("pick", ["a", "b"])
        board.foxes += 1
        handler.flush_terminal_step_reward()
        assert not handler.trajectory
