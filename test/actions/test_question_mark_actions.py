from src.actions.immediate_actions.blue_question_mark import BlueQuestionMarkAction
from src.actions.immediate_actions.grey_question_mark import GreyQuestionMarkAction
from src.actions.immediate_actions.yellow_question_mark import YellowQuestionMarkAction
from src.board.board import Board


class TestQuestionMarkOnFullBoardPart:
    def test_blue_question_mark_returns_no_actions_when_blue_part_is_full(self, stub_input_handler):
        board = Board()
        for box in board.blue_board_part.boxes:
            box.value_used = 2
        assert not BlueQuestionMarkAction().use(board, stub_input_handler)

    def test_yellow_question_mark_returns_no_actions_when_yellow_part_is_full(self, stub_input_handler):
        board = Board()
        for box in board.yellow_board_part.boxes:
            box.is_circled = True
            box.is_crossed = True
        assert not YellowQuestionMarkAction().use(board, stub_input_handler)

    def test_grey_question_mark_returns_no_actions_when_grey_part_is_full(self, stub_input_handler):
        board = Board()
        for box in board.grey_board_part.boxes:
            box.is_crossed = True
        assert not GreyQuestionMarkAction().use(board, stub_input_handler)
