from scripts.train_rl import _curriculum_rounds, TrainingConfig, FeatureFlags


def _config(curriculum=False, iterations=5000, start=2, end=6):
    return TrainingConfig(
        iterations=iterations,
        features=FeatureFlags(
            curriculum=curriculum, max_rounds_start=start, max_rounds_end=end,
        ),
    )


class TestCurriculumRoundsDisabled:
    def test_returns_none_when_disabled(self):
        assert _curriculum_rounds(0, _config(curriculum=False)) is None

    def test_returns_none_midway(self):
        assert _curriculum_rounds(50, _config(curriculum=False, iterations=100)) is None


class TestCurriculumRoundsEnabled:
    def test_first_iteration_returns_start(self):
        assert _curriculum_rounds(0, _config(curriculum=True, iterations=100)) == 2

    def test_last_iteration_returns_end(self):
        assert _curriculum_rounds(99, _config(curriculum=True, iterations=100)) == 6

    def test_midpoint_returns_intermediate(self):
        result = _curriculum_rounds(50, _config(curriculum=True, iterations=100))
        assert 2 <= result <= 6

    def test_single_iteration(self):
        assert _curriculum_rounds(0, _config(curriculum=True, iterations=1)) == 2
