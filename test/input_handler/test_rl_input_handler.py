from src.board.board import Board
from src.game.rl_observer import RLObserver, _MAX_OPTIONS
from src.input_handler.model.rl_input_handler import _build_action_mask


class TestChooseIndex:
    def test_returns_policy_action(self, handler):
        h, policy = handler
        policy.action = 2
        assert h.choose_index("pick", ["a", "b", "c"]) == 2

    def test_passes_correct_num_options(self, handler):
        h, policy = handler
        h.choose_index("pick", ["a", "b", "c", "d"])
        _, mask = policy.calls[0]
        assert sum(mask) == 4

    def test_state_length(self, handler):
        h, policy = handler
        h.choose_index("pick", ["a", "b"])
        state, _ = policy.calls[0]
        assert len(state) == Board.STATE_SIZE + RLObserver.CONTEXT_SIZE


class TestConfirm:
    def test_action_zero_returns_true(self, handler):
        h, policy = handler
        policy.action = 0
        assert h.confirm("accept?") is True

    def test_action_one_returns_false(self, handler):
        h, policy = handler
        policy.action = 1
        assert h.confirm("accept?") is False

    def test_passes_two_options_mask(self, handler):
        h, policy = handler
        h.confirm("accept?")
        _, mask = policy.calls[0]
        assert sum(mask) == 2


class TestChooseValue:
    def test_returns_selected_value(self, handler):
        h, policy = handler
        policy.action = 1
        assert h.choose_value("color?", ["red", "blue", "green"]) == "blue"

    def test_first_value_when_action_zero(self, handler):
        h, policy = handler
        policy.action = 0
        assert h.choose_value("color?", ["red", "blue"]) == "red"


class TestTrajectoryRecording:
    def test_empty_initially(self, handler):
        h, _ = handler
        assert h.trajectory == []

    def test_records_transition_on_choose_index(self, handler):
        h, policy = handler
        policy.action = 0
        policy.log_prob = -1.2
        policy.value = 3.5
        h.choose_index("pick", ["x"])
        assert len(h.trajectory) == 1

    def test_transition_action(self, handler):
        h, policy = handler
        policy.action = 0
        h.choose_index("pick", ["x"])
        assert h.trajectory[0].action == 0

    def test_transition_log_prob(self, handler):
        h, policy = handler
        policy.log_prob = -1.2
        h.choose_index("pick", ["x"])
        assert h.trajectory[0].log_prob == -1.2

    def test_transition_value(self, handler):
        h, policy = handler
        policy.value = 3.5
        h.choose_index("pick", ["x"])
        assert h.trajectory[0].value == 3.5

    def test_accumulates_multiple_transitions(self, handler):
        h, _ = handler
        h.choose_index("a", ["x", "y"])
        h.confirm("b")
        h.choose_value("c", ["r", "g"])
        assert len(h.trajectory) == 3

    def test_clear_trajectory(self, handler):
        h, _ = handler
        h.choose_index("pick", ["x"])
        h.clear_trajectory()
        assert h.trajectory == []

    def test_returned_list_is_copy(self, handler):
        h, _ = handler
        h.choose_index("pick", ["x"])
        traj = h.trajectory
        traj.clear()
        assert len(h.trajectory) == 1


class TestEvalMode:
    def test_no_transitions_stored(self, eval_handler):
        h, _ = eval_handler
        h.choose_index("pick", ["a", "b"])
        assert h.trajectory == []

    def test_still_returns_correct_action(self, eval_handler):
        h, policy = eval_handler
        policy.action = 1
        assert h.choose_index("pick", ["a", "b"]) == 1


class TestBuildActionMask:
    def test_mask_length(self):
        assert len(_build_action_mask(5)) == _MAX_OPTIONS

    def test_first_n_true(self):
        mask = _build_action_mask(3)
        assert mask[:3] == [True, True, True]

    def test_rest_false(self):
        mask = _build_action_mask(3)
        assert all(not v for v in mask[3:])

    def test_zero_options(self):
        assert not any(_build_action_mask(0))
