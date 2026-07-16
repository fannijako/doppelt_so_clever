from src.ui.layout import Layout, MARGIN, MIN_BOARD_HEIGHT, MIN_SCALE, MAX_SCALE, MAX_TOASTS


class TestBoardColumns:
    def test_has_three_columns(self):
        assert len(Layout.compute(1280, 800).board_columns) == 3

    def test_mid_right_of_yellow(self):
        yellow, mid, _ = Layout.compute(1280, 800).board_columns
        assert mid.x >= yellow.right

    def test_grey_right_of_mid(self):
        _, mid, grey = Layout.compute(1280, 800).board_columns
        assert grey.x >= mid.right

    def test_grey_within_right_margin(self):
        assert Layout.compute(1280, 800).grey.right <= 1280 - MARGIN


class TestVerticalStack:
    def test_tray_below_board(self):
        layout = Layout.compute(1280, 800)
        assert layout.tray.y >= layout.yellow.bottom

    def test_action_below_tray(self):
        layout = Layout.compute(1280, 800)
        assert layout.action.y >= layout.tray.bottom


class TestResponsiveClamp:
    def test_board_height_clamped_on_tiny_window(self):
        assert Layout.compute(500, 300).yellow.h >= MIN_BOARD_HEIGHT

    def test_scale_clamped_high_on_huge_window(self):
        assert Layout.compute(4000, 4000).scale == MAX_SCALE

    def test_scale_clamped_low_on_tiny_window(self):
        assert Layout.compute(200, 200).scale == MIN_SCALE


class TestToastSlots:
    def test_count_capped_at_maximum(self):
        assert len(Layout.compute(1280, 800).toast_slots(5)) == MAX_TOASTS

    def test_no_slots_when_empty(self):
        assert Layout.compute(1280, 800).toast_slots(0) == []

    def test_slot_within_grey_right_edge(self):
        layout = Layout.compute(1280, 800)
        assert layout.toast_slots(1)[0].right <= layout.grey.right
