from src.board.board import Board
from src.game.rl_observer import DecisionType, RLObserver


class TestStrategicStateSize:
    def test_strategic_state_appends_feature_block(self):
        observer = RLObserver(Board(), augmented=True, strategic_features=True)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        expected = Board.STATE_SIZE + RLObserver.AUGMENTED_CONTEXT_SIZE + Board.STRATEGIC_FEATURES_SIZE
        assert len(state) == expected

    def test_state_without_strategic_features_unchanged(self):
        observer = RLObserver(Board(), augmented=True, strategic_features=False)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        assert len(state) == Board.STATE_SIZE + RLObserver.AUGMENTED_CONTEXT_SIZE

    def test_strategic_features_default_off(self):
        observer = RLObserver(Board())
        assert observer.strategic_features_enabled is False

    def test_state_size_property_matches_emitted_state(self):
        observer = RLObserver(Board(), augmented=True, strategic_features=True)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        assert len(state) == observer.state_size

    def test_legacy_state_size_property_matches_emitted_state(self):
        observer = RLObserver(Board(), augmented=False, strategic_features=False)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        assert len(state) == observer.state_size

    def test_strategic_block_reflects_board_features(self):
        board = Board()
        observer = RLObserver(board, augmented=True, strategic_features=True)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        assert state[-Board.STRATEGIC_FEATURES_SIZE:] == board.strategic_features()
