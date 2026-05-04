import pytest

from src.board.board import Board
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.game.rl_observer import RLObserver, DecisionType, _MAX_OPTIONS


class TestContextTensorShape:
    def test_context_tensor_length(self, default_context):
        assert len(default_context) == RLObserver.CONTEXT_SIZE

    def test_full_state_length(self, observer):
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3)
        assert len(state) == Board.STATE_SIZE + RLObserver.CONTEXT_SIZE


class TestInitialContextValues:
    def test_round_is_zero(self, default_context):
        assert default_context[0] == 0.0

    def test_subround_is_zero(self, default_context):
        assert default_context[1] == 0.0

    def test_active_flag_is_true(self, default_context):
        assert default_context[2] == 1.0

    def test_all_dice_values_zero(self, default_context):
        assert default_context[3:9] == [0.0] * 6

    def test_all_dice_unavailable(self, default_context):
        assert default_context[9:15] == [0.0] * 6


class TestRoundAndPhaseTracking:
    def test_round_number_normalized(self, observer):
        observer.on_round_started(3)
        ctx = observer.get_context_tensor(DecisionType.CONFIRM, 2)
        assert ctx[0] == pytest.approx(3.0 / 6.0)

    def test_subround_normalized(self, observer):
        observer.on_subround_started(2)
        ctx = observer.get_context_tensor(DecisionType.CONFIRM, 2)
        assert ctx[1] == pytest.approx(2.0 / 3.0)

    def test_active_flag_after_active_round(self, observer):
        observer.on_passive_round_started()
        observer.on_active_round_started()
        ctx = observer.get_context_tensor(DecisionType.CONFIRM, 2)
        assert ctx[2] == 1.0

    def test_passive_flag(self, observer):
        observer.on_passive_round_started()
        ctx = observer.get_context_tensor(DecisionType.CONFIRM, 2)
        assert ctx[2] == 0.0


class TestDiceRolled:
    def test_dice_values_stored(self, observer, six_dice):
        observer.on_dice_rolled(six_dice)
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 1)
        expected = [i / 6.0 for i in range(1, 7)]
        assert ctx[3:9] == pytest.approx(expected)

    def test_all_dice_available(self, observer, six_dice):
        observer.on_dice_rolled(six_dice)
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 1)
        assert ctx[9:15] == [1.0] * 6

    def test_partial_roll_marks_others_unavailable(self, observer):
        partial = [Dice(DiceColor.GREEN), Dice(DiceColor.BLUE)]
        partial[0].value = 3
        partial[1].value = 5
        observer.on_dice_rolled(partial)
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 1)
        assert sum(ctx[9:15]) == 2.0


class TestDiePicked:
    def test_availability_updated_after_pick(self, observer, six_dice):
        observer.on_dice_rolled(six_dice)
        remaining = [six_dice[0], six_dice[2]]
        observer.on_die_picked(six_dice[1], [six_dice[3]], remaining)
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 1)
        assert sum(ctx[9:15]) == 2.0

    def test_empty_available_clears_all(self, observer, six_dice):
        observer.on_dice_rolled(six_dice)
        observer.on_die_picked(six_dice[0], [], [])
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 1)
        assert ctx[9:15] == [0.0] * 6


class TestDecisionTypeOneHot:
    def test_choose_index_one_hot(self, observer):
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 1)
        assert ctx[15:18] == [1.0, 0.0, 0.0]

    def test_confirm_one_hot(self, observer):
        ctx = observer.get_context_tensor(DecisionType.CONFIRM, 1)
        assert ctx[15:18] == [0.0, 1.0, 0.0]

    def test_choose_value_one_hot(self, observer):
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_VALUE, 1)
        assert ctx[15:18] == [0.0, 0.0, 1.0]


class TestNumOptions:
    def test_num_options_normalized(self, observer):
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 15)
        assert ctx[18] == pytest.approx(15.0 / _MAX_OPTIONS)

    def test_num_options_zero(self, observer):
        ctx = observer.get_context_tensor(DecisionType.CHOOSE_INDEX, 0)
        assert ctx[18] == 0.0


class TestScore:
    def test_score_none_initially(self, observer):
        assert observer.score is None

    def test_score_stored_on_game_ended(self, observer):
        observer.on_game_ended(142)
        assert observer.score == 142
