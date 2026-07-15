from src.ui.animations import Animations, ease_out_cubic


def _advance(anim: Animations, steps: int, step: float = 0.1) -> None:
    now = 0.0
    for _ in range(steps):
        now += step
        anim.update(now)


class TestScoreEase:
    def test_initial_displayed_score_is_zero(self):
        assert Animations().displayed_score() == 0

    def test_score_converges_to_target(self):
        anim = Animations()
        anim.set_score(100)
        _advance(anim, 60)
        assert anim.displayed_score() == 100


class TestPulse:
    def test_pulse_starts_at_full_intensity(self):
        anim = Animations()
        anim.pulse(7, 0.0)
        assert anim.pulse_intensity(7, 0.0) == 1.0

    def test_pulse_expires_after_duration(self):
        anim = Animations()
        anim.pulse(7, 0.0)
        anim.update(1.0)
        assert anim.pulse_intensity(7, 1.0) == 0.0


class TestPopups:
    def test_popup_active_within_duration(self):
        anim = Animations()
        anim.add_popup("fox", "pick", 0.0)
        assert len(anim.active_popups(0.1)) == 1

    def test_popup_expires_after_total(self):
        anim = Animations()
        anim.add_popup("fox", "pick", 0.0)
        assert not anim.active_popups(5.0)


class TestEasing:
    def test_ease_out_cubic_endpoints(self):
        assert (ease_out_cubic(0.0), ease_out_cubic(1.0)) == (0.0, 1.0)

    def test_ease_out_cubic_midpoint(self):
        assert ease_out_cubic(0.5) == 0.875
