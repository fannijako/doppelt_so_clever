from pathlib import Path

from src.ui.theme import load_ui_font, font_name_or_fallback, type_size, dim, mix, FONT_NAME


class TestFontLoading:
    def test_bundled_font_loads_by_name(self):
        assert load_ui_font() == FONT_NAME

    def test_missing_font_returns_none(self, monkeypatch):
        monkeypatch.setattr("src.ui.theme.FONT_PATH", Path("/no/such/font.ttf"))
        assert load_ui_font() is None

    def test_fallback_is_a_family_tuple(self):
        assert isinstance(font_name_or_fallback(None), tuple)


class TestTypeScale:
    def test_type_size_scales_with_factor(self):
        assert type_size("body", 2.0) == 36


class TestColorMath:
    def test_mix_midpoint_is_average(self):
        assert mix((0, 0, 0), (100, 100, 100), 0.5) == (50, 50, 50)

    def test_dim_floors_channels(self):
        assert dim((30, 30, 30), 80) == (20, 20, 20)
