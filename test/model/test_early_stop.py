from model.early_stop import EarlyStopTracker


class TestEarlyStopTrackerDisabled:
    def test_never_stops_when_patience_zero(self):
        tracker = EarlyStopTracker(patience=0, smoothing=0.05)
        assert not tracker.step(10.0, {"w": 1})

    def test_not_enabled_when_patience_zero(self):
        tracker = EarlyStopTracker(patience=0, smoothing=0.05)
        assert not tracker.enabled


class TestEarlyStopTrackerStop:
    def test_no_stop_while_improving(self):
        tracker = EarlyStopTracker(patience=3, smoothing=1.0)
        tracker.step(10.0, {})
        tracker.step(20.0, {})
        assert not tracker.step(30.0, {})

    def test_stops_after_patience_exceeded(self):
        tracker = EarlyStopTracker(patience=3, smoothing=1.0)
        tracker.step(100.0, {})
        tracker.step(90.0, {})
        tracker.step(80.0, {})
        assert tracker.step(70.0, {})

    def test_does_not_stop_before_patience(self):
        tracker = EarlyStopTracker(patience=3, smoothing=1.0)
        tracker.step(100.0, {})
        tracker.step(90.0, {})
        assert not tracker.step(80.0, {})

    def test_resets_wait_on_improvement(self):
        tracker = EarlyStopTracker(patience=3, smoothing=1.0)
        tracker.step(100.0, {})
        tracker.step(90.0, {})
        tracker.step(110.0, {})
        tracker.step(100.0, {})
        assert not tracker.step(90.0, {})


class TestEarlyStopTrackerBestState:
    def test_returns_snapshot_at_peak(self):
        tracker = EarlyStopTracker(patience=2, smoothing=1.0)
        tracker.step(100.0, {"w": "best"})
        tracker.step(50.0, {"w": "bad1"})
        tracker.step(40.0, {"w": "bad2"})
        assert tracker.best_state() == {"w": "best"}

    def test_is_deep_copy(self):
        state = {"w": [1, 2, 3]}
        tracker = EarlyStopTracker(patience=5, smoothing=1.0)
        tracker.step(100.0, state)
        state["w"].append(4)
        assert tracker.best_state() == {"w": [1, 2, 3]}

    def test_best_score_tracks_peak(self):
        tracker = EarlyStopTracker(patience=10, smoothing=1.0)
        tracker.step(50.0, {})
        tracker.step(100.0, {})
        tracker.step(75.0, {})
        assert tracker.best_score == 100.0


class TestEarlyStopTrackerSmoothing:
    def test_dampens_spike(self):
        tracker = EarlyStopTracker(patience=3, smoothing=0.1)
        tracker.step(100.0, {})
        tracker.step(200.0, {})
        assert tracker.best_score < 120.0

    def test_smoothing_one_uses_raw_score(self):
        tracker = EarlyStopTracker(patience=3, smoothing=1.0)
        tracker.step(50.0, {})
        tracker.step(100.0, {})
        assert tracker.best_score == 100.0
