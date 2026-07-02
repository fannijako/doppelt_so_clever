import random

import pytest

from src.board.board import Board
from src.actions.action_type import ActionType


def _randomly_filled_board(seed: int) -> Board:
    rng = random.Random(seed)
    board = Board()
    _fill_blue(board, rng)
    _fill_pink(board, rng)
    _fill_green(board, rng)
    _fill_yellow(board, rng)
    _fill_grey(board, rng)
    board.foxes = rng.randint(0, 6)
    return board


def _fill_blue(board: Board, rng: random.Random) -> None:
    for box in board.blue_board_part.boxes[:rng.randint(0, 12)]:
        box.value_used = 5


def _fill_pink(board: Board, rng: random.Random) -> None:
    for box in board.pink_board_part.boxes[:rng.randint(0, 12)]:
        box.value_used = rng.randint(1, 6)


def _fill_green(board: Board, rng: random.Random) -> None:
    for box in board.green_board_part.boxes[:rng.randint(0, 12)]:
        box.add_dice_value(rng.randint(1, 6))


def _fill_yellow(board: Board, rng: random.Random) -> None:
    for box in board.yellow_board_part.boxes:
        if rng.random() < 0.5:
            box.is_circled = True
            box.is_crossed = rng.random() < 0.5


def _fill_grey(board: Board, rng: random.Random) -> None:
    for box in board.grey_board_part.boxes:
        box.is_crossed = rng.random() < 0.4


def _section_scores(board: Board) -> list[int]:
    return [
        board.blue_board_part.evaluate(),
        board.pink_board_part.evaluate(),
        board.green_board_part.evaluate(),
        board.yellow_board_part.evaluate(),
        board.grey_board_part.evaluate(),
    ]


SEEDS = [0, 1, 2, 3, 4, 42, 1337]


@pytest.mark.parametrize("seed", SEEDS)
def test_normalized_scores_match_evaluate_internals(seed):
    board = _randomly_filled_board(seed)
    expected = [
        score / maximum
        for score, maximum in zip(_section_scores(board), (78, 72, 92, 165, 88))
    ]
    assert board.strategic_features()[:5] == expected


@pytest.mark.parametrize("seed", SEEDS)
def test_min_section_value_matches_evaluate_internals(seed):
    board = _randomly_filled_board(seed)
    assert board.strategic_features()[5] == min(_section_scores(board)) / 72


@pytest.mark.parametrize("seed", SEEDS)
def test_min_section_one_hot_marks_argmin(seed):
    board = _randomly_filled_board(seed)
    scores = _section_scores(board)
    assert board.strategic_features()[6:11].index(1.0) == scores.index(min(scores))


@pytest.mark.parametrize("seed", SEEDS)
def test_feature_length_is_pinned(seed):
    board = _randomly_filled_board(seed)
    assert len(board.strategic_features()) == Board.STRATEGIC_FEATURES_SIZE


def test_empty_board_fox_distances_are_maximal(empty_board):
    assert empty_board.strategic_features()[11:] == [1.0, 1.0, 1.0, 1.0, 1.0]


def test_blue_fox_distance_shrinks_as_boxes_fill(empty_board):
    for box in empty_board.blue_board_part.boxes[:3]:
        box.value_used = 5
    assert empty_board.strategic_features()[11] == pytest.approx(6 / 9)


def test_blue_fox_distance_zero_once_fox_box_filled(empty_board):
    for box in empty_board.blue_board_part.boxes[:9]:
        box.value_used = 5
    assert empty_board.strategic_features()[11] == 0.0


def test_green_fox_distance_uses_green_fox_position(empty_board):
    for box in empty_board.green_board_part.boxes[:5]:
        box.add_dice_value(3)
    assert empty_board.strategic_features()[13] == pytest.approx(2 / 7)


def test_yellow_fox_distance_counts_uncircled_column_boxes(empty_board):
    empty_board.yellow_board_part.boxes[1].is_circled = True
    assert empty_board.strategic_features()[14] == pytest.approx(2 / 3)


def test_yellow_fox_distance_zero_after_action_claimed(empty_board):
    empty_board.yellow_board_part.available_columns_for_action.pop(3)
    assert empty_board.strategic_features()[14] == 0.0


def test_grey_fox_distance_counts_uncrossed_column_boxes(empty_board):
    crossed = [box for box in empty_board.grey_board_part.boxes if box.number == 3][:2]
    for box in crossed:
        box.is_crossed = True
    assert empty_board.strategic_features()[15] == pytest.approx(2 / 4)


def test_fox_action_positions_match_distance_assumptions(empty_board):
    positions = (
        next(i for i, box in enumerate(empty_board.blue_board_part.boxes) if box.action == ActionType.FOX),
        next(i for i, box in enumerate(empty_board.pink_board_part.boxes) if box.action == ActionType.FOX),
        next(i for i, box in enumerate(empty_board.green_board_part.boxes) if box.action == ActionType.FOX),
    )
    assert positions == (8, 7, 6)
