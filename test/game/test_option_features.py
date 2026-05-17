from src.actions.not_immediate_actions.reroll_action import ReRollAction
from src.actions.not_immediate_actions.reuse_action import ReUseAction
from src.actions.not_immediate_actions.plus_one_action import PlusOneAction
from src.actions.not_immediate_actions.fox_action import FoxAction
from src.actions.immediate_actions.black_question_mark import BlackQuestionMarkAction
from src.actions.immediate_actions.blue_question_mark import BlueQuestionMarkAction
from src.board.board_parts.yellow_board_part import YellowBoardAction
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.game.option_features import (
    MAX_OPTIONS,
    OPTION_FEATURE_SIZE,
    featurize_options,
    flatten_option_block,
)


_BLUE_SLOT = 1 + list(DiceColor).index(DiceColor.BLUE)
_GREEN_SLOT = 1 + list(DiceColor).index(DiceColor.GREEN)
_YELLOW_SLOT = 1 + list(DiceColor).index(DiceColor.YELLOW)


class TestDiceOptions:
    def test_color_one_hot_set_for_blue_die(self):
        die = Dice(DiceColor.BLUE)
        die.set_value(3)
        feat = featurize_options([die])[0]
        assert feat[_BLUE_SLOT] == 1.0

    def test_value_slot_normalized(self):
        die = Dice(DiceColor.BLUE)
        die.set_value(6)
        feat = featurize_options([die])[0]
        assert feat[7] == 1.0

    def test_unrolled_die_has_zero_value_slot(self):
        feat = featurize_options([Dice(DiceColor.BLUE)])[0]
        assert feat[7] == 0.0

    def test_index_slot_increases(self):
        dice = [Dice(DiceColor.BLUE), Dice(DiceColor.BLUE)]
        feats = featurize_options(dice)
        assert feats[0][0] == 0.0
        assert feats[1][0] == 1.0 / MAX_OPTIONS


class TestColorStringOptions:
    def test_blue_string_lights_blue_slot(self):
        feat = featurize_options(["blue"])[0]
        assert feat[_BLUE_SLOT] == 1.0

    def test_green_string_lights_green_slot(self):
        feat = featurize_options(["green"])[0]
        assert feat[_GREEN_SLOT] == 1.0

    def test_yes_no_only_index_slots(self):
        feats = featurize_options(["yes", "no"])
        for f in feats:
            assert sum(f[1:]) == 0.0


class TestPlacementTuples:
    def test_yellow_four_tuple_sets_row_col_marker(self):
        feat = featurize_options([(4, 2, 3, YellowBoardAction.CIRCLE)])[0]
        assert feat[7] == 4 / 6.0
        assert feat[8] == 2 / 4.0
        assert feat[9] == 3 / 6.0
        assert feat[10] == 1.0

    def test_yellow_three_tuple_sets_row_col_marker(self):
        feat = featurize_options([(1, 2, YellowBoardAction.CROSS)])[0]
        assert feat[8] == 1 / 4.0
        assert feat[9] == 2 / 6.0
        assert feat[10] == 0.0

    def test_grey_color_value_tuple(self):
        feat = featurize_options([(DiceColor.YELLOW, 5)])[0]
        assert feat[_YELLOW_SLOT] == 1.0
        assert feat[7] == 5 / 6.0


class TestActionOptions:
    def test_reroll_action_bucket(self):
        feat = featurize_options([ReRollAction()])[0]
        reroll_action_bucket = feat[11]
        feat_b = featurize_options([BlackQuestionMarkAction()])[0]
        black_bucket = feat_b[11]
        assert reroll_action_bucket != black_bucket

    def test_reuse_and_reroll_same_bucket(self):
        a = featurize_options([ReRollAction()])[0][11]
        b = featurize_options([ReUseAction()])[0][11]
        c = featurize_options([PlusOneAction()])[0][11]
        assert a == b == c

    def test_fox_and_question_mark_differ(self):
        a = featurize_options([FoxAction()])[0][11]
        b = featurize_options([BlueQuestionMarkAction()])[0][11]
        assert a != b


class TestYellowBoardActionOption:
    def test_circle_marker_bit_set(self):
        feat = featurize_options([YellowBoardAction.CIRCLE])[0]
        assert feat[10] == 1.0

    def test_cross_marker_bit_zero(self):
        feat = featurize_options([YellowBoardAction.CROSS])[0]
        assert feat[10] == 0.0


class TestEdgeCases:
    def test_empty_options_returns_empty_list(self):
        assert featurize_options([]) == []

    def test_none_options_returns_empty_list(self):
        assert featurize_options(None) == []

    def test_truncates_to_max_options(self):
        many = [Dice(DiceColor.BLUE)] * (MAX_OPTIONS + 5)
        assert len(featurize_options(many)) == MAX_OPTIONS

    def test_flatten_pads_to_full_block(self):
        feats = featurize_options([Dice(DiceColor.BLUE)])
        block = flatten_option_block(feats)
        assert len(block) == MAX_OPTIONS * OPTION_FEATURE_SIZE
        assert all(v == 0.0 for v in block[OPTION_FEATURE_SIZE:])
