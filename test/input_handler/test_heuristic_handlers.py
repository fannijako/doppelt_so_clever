from src.actions.action_handler import ActionHandler
from src.game.game import Game
from src.game.logging_observer import LoggingObserver
from src.input_handler.heuristics.fox_balancing import FoxBalancingInputHandler
from src.input_handler.heuristics.greedy_immediate import GreedyImmediateInputHandler
from src.input_handler.heuristics.resource_aware import ResourceAwareInputHandler


class TestGreedyImmediate:
    def test_confirms_place_die(self, board):
        assert GreedyImmediateInputHandler(board).confirm("Place die blue|6? (y/n): ") is True

    def test_confirms_use_reuse(self, board):
        assert GreedyImmediateInputHandler(board).confirm("Use a reuse? (y/n): ") is True

    def test_color_pick_prefers_most_empty_section(self, board):
        for i in range(11):
            board.green_board_part.boxes[i].value_used = 1
        choice = GreedyImmediateInputHandler(board).choose_value(
            "Pick an available color: ", ["green", "blue"],
        )
        assert choice == "blue"

    def test_falls_back_to_random_when_no_color_options(self, board):
        choice = GreedyImmediateInputHandler(board).choose_value(
            "Pick an available color: ", ["white"],
        )
        assert choice == "white"

    def test_plays_full_game_without_error(self, board):
        handler = GreedyImmediateInputHandler(board)
        score = Game(
            input_handler=handler, board=board,
            observer=LoggingObserver(), action_handler=ActionHandler(board=board),
        ).play()
        assert isinstance(score, int)


class TestFoxBalancing:
    def test_confirms_place_die(self, board):
        assert FoxBalancingInputHandler(board).confirm("Place die blue|6? (y/n): ") is True

    def test_does_not_force_reuse(self, board):
        handler = FoxBalancingInputHandler(board)
        results = {handler.confirm("Use a reuse? (y/n): ") for _ in range(20)}
        assert results == {True, False}

    def test_color_pick_prefers_lowest_scoring_section(self, board):
        for i in range(3):
            board.pink_board_part.boxes[i].value_used = 5
        choice = FoxBalancingInputHandler(board).choose_value(
            "Pick an available color: ", ["pink", "blue"],
        )
        assert choice == "blue"

    def test_plays_full_game_without_error(self, board):
        handler = FoxBalancingInputHandler(board)
        score = Game(
            input_handler=handler, board=board,
            observer=LoggingObserver(), action_handler=ActionHandler(board=board),
        ).play()
        assert isinstance(score, int)


class TestResourceAware:
    def test_confirms_place_die(self, board):
        assert ResourceAwareInputHandler(board).confirm("Place die blue|6? (y/n): ") is True

    def test_confirms_use_reuse(self, board):
        assert ResourceAwareInputHandler(board).confirm("Use a reuse? (y/n): ") is True

    def test_reroll_blocked_when_fewer_than_two_usable(self, board):
        board.usable_rerolls = 1
        assert ResourceAwareInputHandler(board).confirm("Use a reroll? (y/n): ") is False

    def test_reroll_allowed_when_two_or_more_usable(self, board):
        board.usable_rerolls = 2
        assert ResourceAwareInputHandler(board).confirm("Use a reroll? (y/n): ") is True

    def test_plus_one_blocked_below_two_foxes(self, board):
        board.foxes = 1
        assert ResourceAwareInputHandler(board).confirm("Use a plus one? (y/n): ") is False

    def test_plus_one_allowed_at_two_foxes(self, board):
        board.foxes = 2
        assert ResourceAwareInputHandler(board).confirm("Use a plus one? (y/n): ") is True

    def test_plays_full_game_without_error(self, board):
        handler = ResourceAwareInputHandler(board)
        score = Game(
            input_handler=handler, board=board,
            observer=LoggingObserver(), action_handler=ActionHandler(board=board),
        ).play()
        assert isinstance(score, int)
