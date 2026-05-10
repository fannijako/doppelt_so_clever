from src.board.board import Board
from src.game.rl_observer import RLObserver


class TestObserverFinalScoreOnly:
    def test_score_none_before_game_ends(self):
        observer = RLObserver(Board())
        assert observer.score is None

    def test_score_set_on_game_ended(self):
        observer = RLObserver(Board())
        observer.on_game_ended(142)
        assert observer.score == 142

    def test_board_updated_has_no_reward_side_effect(self):
        observer = RLObserver(Board())
        observer.on_board_updated()
        assert observer.score is None
