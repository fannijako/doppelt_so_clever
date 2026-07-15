from src.ui.layout import (
    Layout, MARGIN, MIN_ROW_HEIGHT, MAX_POPUPS, POPUP_HEIGHT, POPUP_GAP, MIN_SCALE, MAX_SCALE,
)


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

    def test_scale_clamped_high_on_huge_window(self):
        assert Layout.compute(4000, 4000).scale == MAX_SCALE

    def test_scale_clamped_low_on_tiny_window(self):
        assert Layout.compute(200, 200).scale == MIN_SCALE


class TestPopupPlacement:
    def test_popup_origin_inside_won_actions(self):
        layout = Layout.compute(1280, 800)
        assert layout.won_actions.collidepoint(layout.popup_origin())

    def test_popup_stack_fits_inside_won_actions(self):
        layout = Layout.compute(1280, 800)
        stack = MAX_POPUPS * round((POPUP_HEIGHT + POPUP_GAP) * layout.scale)
        assert layout.popup_origin()[1] + stack <= layout.won_actions.bottom
