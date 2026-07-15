from pathlib import Path

from src.ui.theme import load_fonts, Fonts


class TestFontLoading:
    def test_load_fonts_returns_font_set(self):
        assert isinstance(load_fonts(), Fonts)

    def test_fallback_when_bundled_font_missing(self, monkeypatch):
        monkeypatch.setattr("src.ui.theme.FONT_PATH", Path("/no/such/font.ttf"))
        assert isinstance(load_fonts(), Fonts)
