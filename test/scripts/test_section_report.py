from scripts.section_report import GameStats, format_report


def _stats() -> list[GameStats]:
    return [
        GameStats(total=120, sections=(10, 20, 40, 5, 45), foxes=2),
        GameStats(total=150, sections=(30, 25, 40, 15, 40), foxes=1),
    ]


class TestGameStats:
    def test_min_section_index_picks_lowest(self):
        assert _stats()[0].min_section_index == 3

    def test_fox_bonus_multiplies_min_section(self):
        assert _stats()[0].fox_bonus == 2 * 5


class TestFormatReport:
    def test_reports_total_mean(self):
        assert "mean=135.0" in format_report(_stats())

    def test_reports_section_mean(self):
        blue_line = next(line for line in format_report(_stats()).splitlines() if "blue" in line)
        assert blue_line.split() == ["blue", "20.0"]

    def test_reports_min_section_share(self):
        assert "yellow 100.0%" in format_report(_stats())

    def test_reports_foxes_per_game(self):
        assert "foxes/game=1.50" in format_report(_stats())

    def test_reports_threshold_share(self):
        assert ">=140: 50.0%" in format_report(_stats())
