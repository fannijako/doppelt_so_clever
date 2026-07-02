import pytest

from src.board.board import Board
from src.actions.action_type import ActionType


BLUE_FILLED_BOXES_TO_POINTS = [
    (0, 0), (1, 1), (2, 3), (3, 6), (4, 10), (5, 15), (6, 21),
    (7, 28), (8, 36), (9, 45), (10, 55), (11, 66), (12, 78),
]

YELLOW_CROSSED_BOXES_TO_POINTS = [
    (0, 0), (1, 3), (2, 10), (3, 21), (4, 36),
    (5, 55), (6, 75), (7, 96), (8, 118), (9, 141), (10, 165),
]

GREY_ROW_CROSSED_BOXES_TO_POINTS = [
    (0, 0), (1, 2), (2, 4), (3, 7), (4, 11), (5, 16), (6, 22),
]

GREEN_WRITTEN_VALUES_TO_POINTS = [
    ([], 0),
    ([6], 0),
    ([6, 2], 4),
    ([6, 2, 9], 4),
    ([6, 2, 9, 3], 10),
    ([2, 6], -4),
]


def _fill_first_blue_boxes(board: Board, count: int) -> None:
    for box in board.blue_board_part.boxes[:count]:
        box.value_used = 5


def _cross_first_yellow_boxes(board: Board, count: int) -> None:
    for box in board.yellow_board_part.boxes[:count]:
        box.is_crossed = True


def _cross_first_grey_row_boxes(board: Board, count: int) -> None:
    for box in board.grey_board_part.boxes[:count]:
        box.is_crossed = True


def _set_green_written_values(board: Board, values: list[int]) -> None:
    for box, value in zip(board.green_board_part.boxes, values):
        box.value_used = value


@pytest.mark.parametrize("filled_boxes, expected_points", BLUE_FILLED_BOXES_TO_POINTS)
def test_blue_scores_by_filled_box_count(empty_board, filled_boxes, expected_points):
    _fill_first_blue_boxes(empty_board, filled_boxes)
    assert empty_board.blue_board_part.evaluate() == expected_points


@pytest.mark.parametrize("crossed_boxes, expected_points", YELLOW_CROSSED_BOXES_TO_POINTS)
def test_yellow_scores_by_crossed_box_count(empty_board, crossed_boxes, expected_points):
    _cross_first_yellow_boxes(empty_board, crossed_boxes)
    assert empty_board.yellow_board_part.evaluate() == expected_points


@pytest.mark.parametrize("crossed_boxes, expected_points", GREY_ROW_CROSSED_BOXES_TO_POINTS)
def test_grey_scores_each_row_by_crossed_box_count(empty_board, crossed_boxes, expected_points):
    _cross_first_grey_row_boxes(empty_board, crossed_boxes)
    assert empty_board.grey_board_part.evaluate() == expected_points


def test_grey_sums_all_four_rows(empty_board):
    for box in empty_board.grey_board_part.boxes:
        box.is_crossed = True
    assert empty_board.grey_board_part.evaluate() == 4 * 22


def test_pink_scores_sum_of_written_values(empty_board):
    for box, value in zip(empty_board.pink_board_part.boxes, [4, 2, 6, 5]):
        box.value_used = value
    assert empty_board.pink_board_part.evaluate() == 17


@pytest.mark.parametrize("written_values, expected_points", GREEN_WRITTEN_VALUES_TO_POINTS)
def test_green_scores_pairwise_first_minus_second(empty_board, written_values, expected_points):
    _set_green_written_values(empty_board, written_values)
    assert empty_board.green_board_part.evaluate() == expected_points


def test_green_multiplies_die_value_by_box_multiplier(empty_board):
    empty_board.green_board_part.boxes[0].add_dice_value(3)
    assert empty_board.green_board_part.boxes[0].value_used == 3 * 2


def test_each_fox_scores_the_lowest_section(empty_board):
    _fill_first_blue_boxes(empty_board, 3)
    empty_board.pink_board_part.boxes[0].value_used = 4
    _set_green_written_values(empty_board, [6, 2])
    _cross_first_yellow_boxes(empty_board, 1)
    _cross_first_grey_row_boxes(empty_board, 1)
    empty_board.foxes = 3
    empty_board.game_over = True
    assert empty_board.evaluate() == (6 + 4 + 4 + 3 + 2) + 3 * 2


def test_foxes_are_worthless_when_a_section_scores_zero(empty_board):
    _fill_first_blue_boxes(empty_board, 3)
    empty_board.pink_board_part.boxes[0].value_used = 4
    _set_green_written_values(empty_board, [6, 2])
    _cross_first_yellow_boxes(empty_board, 1)
    empty_board.foxes = 3
    empty_board.game_over = True
    assert empty_board.evaluate() == (6 + 4 + 4 + 3 + 0) + 3 * 0


def test_fox_action_sits_on_a_reachable_green_box(empty_board):
    fox_box_indices = [
        box.index for box in empty_board.green_board_part.boxes if box.action == ActionType.FOX
    ]
    assert fox_box_indices == [6]


def test_fox_action_reachable_in_yellow_and_grey_columns(empty_board):
    yellow_fox = empty_board.yellow_board_part.available_columns_for_action[3]
    grey_fox = empty_board.grey_board_part.available_columns_for_action[3]
    assert (yellow_fox, grey_fox) == (ActionType.FOX, ActionType.FOX)
