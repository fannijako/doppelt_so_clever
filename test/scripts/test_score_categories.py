import pytest

from scripts.evaluate_rl import (
    _CATEGORY_LABELS,
    _category_distribution,
    _category_index,
)
from src.game.score_rating import SCORE_CATEGORIES


class TestCategoryIndex:
    def test_score_below_first_bucket_goes_to_first(self):
        assert _category_index(0) == 0

    def test_boundary_falls_in_next_bucket(self):
        assert _category_index(140) == 1

    def test_just_below_boundary_stays_in_current_bucket(self):
        assert _category_index(139) == 0

    def test_open_upper_bucket_captures_high_scores(self):
        assert _category_index(500) == len(SCORE_CATEGORIES) - 1


class TestCategoryDistribution:
    def test_percentages_sum_to_100(self):
        scores = [10, 140, 160, 200, 320]
        total = sum(_category_distribution(scores))
        assert pytest.approx(total, abs=0.01) == 100.0

    def test_uniform_split(self):
        scores = [10, 150]
        dist = _category_distribution(scores)
        assert (dist[0], dist[1]) == (50.0, 50.0)

    def test_empty_scores_returns_zeros(self):
        assert _category_distribution([]) == [0.0] * len(SCORE_CATEGORIES)


class TestCategoryLabels:
    def test_first_label_uses_less_than(self):
        assert _CATEGORY_LABELS[0] == "<140"

    def test_middle_label_is_inclusive_range(self):
        assert _CATEGORY_LABELS[1] == "140-159"

    def test_open_top_label_uses_ge(self):
        assert _CATEGORY_LABELS[-1] == ">=320"
