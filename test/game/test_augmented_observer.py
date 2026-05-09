from src.board.board import Board
from src.game.rl_observer import (
    RLObserver,
    DecisionType,
    PROMPT_FEATURES_SIZE,
)


class TestAugmentedState:
    def test_augmented_state_longer_than_standard(self):
        observer = RLObserver(Board(), augmented=True)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        base_size = Board.STATE_SIZE + RLObserver.CONTEXT_SIZE
        assert len(state) == base_size + PROMPT_FEATURES_SIZE

    def test_non_augmented_state_unchanged(self):
        observer = RLObserver(Board(), augmented=False)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        assert len(state) == Board.STATE_SIZE + RLObserver.CONTEXT_SIZE

    def test_context_size_property_augmented(self):
        observer = RLObserver(Board(), augmented=True)
        assert observer.context_size == RLObserver.AUGMENTED_CONTEXT_SIZE

    def test_context_size_property_standard(self):
        observer = RLObserver(Board(), augmented=False)
        assert observer.context_size == RLObserver.CONTEXT_SIZE

    def test_augmented_context_size_equals_base_plus_prompt(self):
        assert RLObserver.AUGMENTED_CONTEXT_SIZE == RLObserver.CONTEXT_SIZE + PROMPT_FEATURES_SIZE
