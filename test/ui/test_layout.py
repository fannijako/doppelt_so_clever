from src.ui.layout import Layout, MARGIN, MIN_ROW_HEIGHT


class TestTopPanels:
    def test_has_three_panels(self):
        assert len(Layout.compute(1280, 800).top_panels) == 3

    def test_panels_do_not_overlap(self):
        panels = Layout.compute(1280, 800).top_panels
        assert panels[1].x >= panels[0].right

    def test_last_panel_stays_within_right_margin(self):
        panels = Layout.compute(1280, 800).top_panels
        assert panels[-1].right <= 1280 - MARGIN


class TestSecondRow:
    def test_dice_panel_below_top_row(self):
        layout = Layout.compute(1280, 800)
        assert layout.dice_panel.y >= layout.top_panels[0].bottom

    def test_won_actions_left_of_dice_panel(self):
        layout = Layout.compute(1280, 800)
        assert layout.won_actions.right <= layout.dice_panel.x


class TestResponsiveClamp:
    def test_row_height_clamped_on_tiny_window(self):
        assert Layout.compute(400, 200).top_panels[0].height >= MIN_ROW_HEIGHT

    def test_prompt_below_status(self):
        layout = Layout.compute(1280, 800)
        assert layout.prompt_y > layout.status_y
