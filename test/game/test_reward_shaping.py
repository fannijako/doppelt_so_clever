from dataclasses import replace

import pytest

from src.board.board import Board
from src.game.reward_shaper import (
    MIN_SECTION_PBRS_REWARD_CONFIG,
    YELLOW_DEPTH_PBRS_REWARD_CONFIG,
    BoardSnapshot,
    RewardConfig,
    RewardShaper,
)
from src.game.rl_observer import RLObserver


_BASE = BoardSnapshot(
    filled_boxes=0, foxes=0,
    gained_rerolls=0, gained_plus_ones=0, gained_reuses=0,
    consumed_immediate_actions=0,
    failed_action_count=0, partial_score=None,
)


def _snapshot(**overrides) -> BoardSnapshot:
    return replace(_BASE, **overrides)


class TestObserverFinalScoreOnly:
    def test_score_none_before_game_ends(self):
        observer = RLObserver(Board())
        assert observer.score is None

    def test_score_set_on_game_ended(self):
        observer = RLObserver(Board())
        observer.on_game_ended(142)
        assert observer.score == 142


class TestRewardShaperDeltas:
    def test_no_change_yields_zero(self):
        shaper = RewardShaper()
        prev = _snapshot()
        curr = _snapshot()
        assert shaper.compute(prev, curr) == 0.0

    def test_box_delta_positive_reward(self):
        shaper = RewardShaper(RewardConfig(w_box=0.5))
        reward = shaper.compute(_snapshot(filled_boxes=2), _snapshot(filled_boxes=5))
        assert reward == pytest.approx(0.5 * 3)

    def test_fox_delta_positive_reward(self):
        shaper = RewardShaper(RewardConfig(w_fox=1.0))
        reward = shaper.compute(_snapshot(foxes=0), _snapshot(foxes=2))
        assert reward == pytest.approx(2.0)

    def test_plus_one_gain_positive_reward(self):
        shaper = RewardShaper(RewardConfig(w_plus_one=1.0))
        reward = shaper.compute(_snapshot(), _snapshot(gained_plus_ones=2))
        assert reward == pytest.approx(2.0)

    def test_reroll_gain_positive_reward(self):
        shaper = RewardShaper(RewardConfig(w_reroll=0.3))
        reward = shaper.compute(_snapshot(), _snapshot(gained_rerolls=2))
        assert reward == pytest.approx(0.6)

    def test_reuse_gain_positive_reward(self):
        shaper = RewardShaper(RewardConfig(w_reuse=0.3))
        reward = shaper.compute(_snapshot(), _snapshot(gained_reuses=2))
        assert reward == pytest.approx(0.6)

    def test_consumed_immediate_action_positive_reward(self):
        shaper = RewardShaper(RewardConfig(w_consumed_immediate=1.0))
        reward = shaper.compute(_snapshot(), _snapshot(consumed_immediate_actions=3))
        assert reward == pytest.approx(3.0)

    def test_plus_one_outweighs_reroll_at_default_weights(self):
        shaper = RewardShaper(RewardConfig())
        plus_one_reward = shaper.compute(_snapshot(), _snapshot(gained_plus_ones=1))
        reroll_reward = shaper.compute(_snapshot(), _snapshot(gained_rerolls=1))
        assert plus_one_reward > reroll_reward

    def test_failed_action_yields_negative_reward(self):
        shaper = RewardShaper(RewardConfig(w_failed=2.0))
        reward = shaper.compute(
            _snapshot(failed_action_count=0),
            _snapshot(failed_action_count=1),
        )
        assert reward == pytest.approx(-2.0)


class TestPartialScoreFlag:
    def test_partial_score_ignored_when_flag_off(self):
        shaper = RewardShaper(RewardConfig(use_partial_score=False, w_score=1.0))
        reward = shaper.compute(
            _snapshot(partial_score=10.0),
            _snapshot(partial_score=20.0),
        )
        assert reward == pytest.approx(0.0)

    def test_partial_score_contributes_when_flag_on(self):
        shaper = RewardShaper(RewardConfig(use_partial_score=True, w_score=0.1))
        reward = shaper.compute(
            _snapshot(partial_score=10.0),
            _snapshot(partial_score=30.0),
        )
        assert reward == pytest.approx(0.1 * 20.0)


class TestMinSectionShaping:
    def test_min_section_gain_rewarded(self):
        shaper = RewardShaper(MIN_SECTION_PBRS_REWARD_CONFIG)
        reward = shaper.compute(
            _snapshot(min_section_score=0),
            _snapshot(min_section_score=4),
        )
        assert reward == pytest.approx(0.1 * 4)

    def test_min_section_drop_penalized(self):
        shaper = RewardShaper(MIN_SECTION_PBRS_REWARD_CONFIG)
        reward = shaper.compute(
            _snapshot(min_section_score=6),
            _snapshot(min_section_score=2),
        )
        assert reward == pytest.approx(-0.1 * 4)

    def test_breadth_progress_not_rewarded(self):
        shaper = RewardShaper(MIN_SECTION_PBRS_REWARD_CONFIG)
        reward = shaper.compute(
            _snapshot(min_section_score=2),
            _snapshot(filled_boxes=5, foxes=1, gained_plus_ones=2, min_section_score=2),
        )
        assert reward == pytest.approx(0.0)

    def test_contributions_telescope_across_snapshot_chain(self):
        shaper = RewardShaper(MIN_SECTION_PBRS_REWARD_CONFIG)
        chain = [_snapshot(min_section_score=s) for s in (0, 3, 1, 1, 7, 5)]
        total = sum(shaper.compute(prev, curr) for prev, curr in zip(chain, chain[1:]))
        assert total == pytest.approx(0.1 * (5 - 0))

    def test_capture_records_min_section_when_configured(self):
        board = Board()
        snapshot = BoardSnapshot.capture(board, RLObserver(board), MIN_SECTION_PBRS_REWARD_CONFIG)
        assert snapshot.min_section_score == 0

    def test_capture_skips_min_section_when_not_configured(self):
        board = Board()
        snapshot = BoardSnapshot.capture(board, RLObserver(board), RewardConfig())
        assert snapshot.min_section_score is None


class TestYellowDepthShaping:
    def test_yellow_cross_gain_rewarded(self):
        shaper = RewardShaper(YELLOW_DEPTH_PBRS_REWARD_CONFIG)
        reward = shaper.compute(
            _snapshot(yellow_crossed=2),
            _snapshot(yellow_crossed=4),
        )
        assert reward == pytest.approx(0.1 * 2)

    def test_min_section_term_still_active_in_composed_config(self):
        shaper = RewardShaper(YELLOW_DEPTH_PBRS_REWARD_CONFIG)
        reward = shaper.compute(
            _snapshot(min_section_score=0, yellow_crossed=0),
            _snapshot(min_section_score=3, yellow_crossed=1),
        )
        assert reward == pytest.approx(0.1 * 3 + 0.1 * 1)

    def test_breadth_progress_not_rewarded(self):
        shaper = RewardShaper(YELLOW_DEPTH_PBRS_REWARD_CONFIG)
        reward = shaper.compute(
            _snapshot(yellow_crossed=3),
            _snapshot(filled_boxes=5, foxes=1, gained_plus_ones=2, yellow_crossed=3),
        )
        assert reward == pytest.approx(0.0)

    def test_contributions_telescope_across_snapshot_chain(self):
        shaper = RewardShaper(YELLOW_DEPTH_PBRS_REWARD_CONFIG)
        chain = [_snapshot(yellow_crossed=c) for c in (0, 1, 1, 4, 6)]
        total = sum(shaper.compute(prev, curr) for prev, curr in zip(chain, chain[1:]))
        assert total == pytest.approx(0.1 * (6 - 0))

    def test_capture_records_yellow_crossed_when_configured(self):
        board = Board()
        snapshot = BoardSnapshot.capture(board, RLObserver(board), YELLOW_DEPTH_PBRS_REWARD_CONFIG)
        assert snapshot.yellow_crossed == 0

    def test_capture_skips_yellow_crossed_when_not_configured(self):
        board = Board()
        snapshot = BoardSnapshot.capture(board, RLObserver(board), MIN_SECTION_PBRS_REWARD_CONFIG)
        assert snapshot.yellow_crossed is None
