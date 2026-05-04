import pytest

from src.board.board import Board


class TestBoardToTensorShape:
    def test_output_length_matches_state_size(self, empty_tensor):
        assert len(empty_tensor) == Board.STATE_SIZE

    def test_all_values_in_zero_one_range(self, empty_tensor):
        assert all(0.0 <= v <= 1.0 for v in empty_tensor)


class TestEmptyBoardFilledFlags:
    def test_blue_boxes_not_filled(self, empty_tensor):
        assert all(empty_tensor[i * 3 + 2] == 0.0 for i in range(12))

    def test_green_boxes_not_filled(self, empty_tensor):
        assert all(empty_tensor[36 + i * 3 + 2] == 0.0 for i in range(12))

    def test_pink_boxes_not_filled(self, empty_tensor):
        assert all(empty_tensor[72 + i * 3 + 2] == 0.0 for i in range(12))


class TestEmptyBoardYellow:
    def test_no_boxes_circled(self, empty_tensor):
        assert all(empty_tensor[108 + i * 5 + 3] == 0.0 for i in range(10))

    def test_no_boxes_crossed(self, empty_tensor):
        assert all(empty_tensor[108 + i * 5 + 4] == 0.0 for i in range(10))


class TestEmptyBoardGreyActionsResources:
    def test_grey_no_boxes_crossed(self, empty_tensor):
        assert all(empty_tensor[158 + i * 8 + 7] == 0.0 for i in range(24))

    def test_all_actions_available(self, empty_tensor):
        assert all(v == 1.0 for v in empty_tensor[350:365])

    def test_resource_count(self, empty_tensor):
        assert len(empty_tensor[365:]) == 7

    def test_all_resources_zero(self, empty_tensor):
        assert all(v == 0.0 for v in empty_tensor[365:])


class TestModifiedBoardResources:
    @pytest.fixture()
    def resource_board(self):
        board = Board()
        board.foxes = 3
        board.gained_rerolls = 2
        board.usable_rerolls = 1
        return board

    def test_foxes(self, resource_board):
        assert resource_board.to_tensor()[365] == pytest.approx(3.0 / 6.0)

    def test_gained_rerolls(self, resource_board):
        assert resource_board.to_tensor()[366] == pytest.approx(2.0 / 6.0)

    def test_usable_rerolls(self, resource_board):
        assert resource_board.to_tensor()[367] == pytest.approx(1.0 / 6.0)


class TestBlueBoxFilled:
    def test_first_box_value_used(self, filled_blue_board):
        assert filled_blue_board.to_tensor()[0] == pytest.approx(7.0 / 12.0)

    def test_first_box_max_limit(self, filled_blue_board):
        assert filled_blue_board.to_tensor()[1] == pytest.approx(12.0 / 12.0)

    def test_first_box_is_filled(self, filled_blue_board):
        assert filled_blue_board.to_tensor()[2] == 1.0

    def test_second_box_value_used_zero(self, filled_blue_board):
        assert filled_blue_board.to_tensor()[3] == pytest.approx(0.0)

    def test_second_box_max_limit_lowered(self, filled_blue_board):
        assert filled_blue_board.to_tensor()[4] == pytest.approx(7.0 / 12.0)

    def test_second_box_not_filled(self, filled_blue_board):
        assert filled_blue_board.to_tensor()[5] == 0.0


class TestGreyColorOneHot:
    def test_first_box_is_yellow(self, empty_tensor):
        assert empty_tensor[158 + 3] == 1.0

    def test_first_box_one_hot_sums_to_one(self, empty_tensor):
        assert sum(empty_tensor[158:158 + 6]) == 1.0

    def test_seventh_box_is_blue(self, empty_tensor):
        assert empty_tensor[158 + 6 * 8 + 1] == 1.0

    def test_seventh_box_one_hot_sums_to_one(self, empty_tensor):
        assert sum(empty_tensor[158 + 6 * 8:158 + 6 * 8 + 6]) == 1.0

    def test_tensor_is_deterministic(self, empty_board):
        assert empty_board.to_tensor() == empty_board.to_tensor()
