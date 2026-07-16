from src.ui.geometry import Rect


class TestRect:
    def test_right_edge(self):
        assert Rect(10, 20, 30, 40).right == 40

    def test_bottom_edge(self):
        assert Rect(10, 20, 30, 40).bottom == 60

    def test_center_point(self):
        assert Rect(0, 0, 10, 10).center == (5, 5)

    def test_collidepoint_inside(self):
        assert Rect(0, 0, 10, 10).collidepoint(5, 5)

    def test_collidepoint_outside(self):
        assert not Rect(0, 0, 10, 10).collidepoint(20, 20)

    def test_inflate_grows_symmetrically(self):
        assert Rect(10, 10, 10, 10).inflate(4, 4) == Rect(8, 8, 14, 14)
