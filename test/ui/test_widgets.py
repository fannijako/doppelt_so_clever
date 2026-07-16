from src.ui.widgets import pip_offsets


class TestPipOffsets:
    def test_pip_count_matches_value(self):
        assert [len(pip_offsets(value)) for value in range(1, 7)] == [1, 2, 3, 4, 5, 6]

    def test_single_pip_is_centered(self):
        assert pip_offsets(1) == [(0.5, 0.5)]

    def test_all_offsets_inside_unit_square(self):
        points = [point for value in range(1, 7) for point in pip_offsets(value)]
        assert all(0.0 < x < 1.0 and 0.0 < y < 1.0 for x, y in points)

    def test_unknown_value_has_no_pips(self):
        assert pip_offsets(0) == []
