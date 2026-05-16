from src.board.board import Board
from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.game.option_features import OPTION_BLOCK_SIZE, OPTION_FEATURE_SIZE
from src.game.rl_observer import (
    PROMPT_FEATURES_SIZE,
    DecisionType,
    RLObserver,
)


class TestAugmentedStateSize:
    def test_augmented_state_includes_prompt_and_option_block(self):
        observer = RLObserver(Board(), augmented=True)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        expected = Board.STATE_SIZE + RLObserver.CONTEXT_SIZE + PROMPT_FEATURES_SIZE + OPTION_BLOCK_SIZE
        assert len(state) == expected

    def test_non_augmented_state_unchanged(self):
        observer = RLObserver(Board(), augmented=False)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 3, "Pick an available color: ")
        assert len(state) == Board.STATE_SIZE + RLObserver.CONTEXT_SIZE

    def test_augmented_context_size_equals_base_plus_prompt_plus_option_block(self):
        assert RLObserver.AUGMENTED_CONTEXT_SIZE == (
            RLObserver.CONTEXT_SIZE + PROMPT_FEATURES_SIZE + OPTION_BLOCK_SIZE
        )

    def test_context_size_property_augmented(self):
        observer = RLObserver(Board(), augmented=True)
        assert observer.context_size == RLObserver.AUGMENTED_CONTEXT_SIZE

    def test_context_size_property_standard(self):
        observer = RLObserver(Board(), augmented=False)
        assert observer.context_size == RLObserver.CONTEXT_SIZE


class TestAliasing:
    def _state(self, num_options, prompt, options=None):
        observer = RLObserver(Board(), augmented=True)
        return observer.get_state(DecisionType.CHOOSE_INDEX, num_options, prompt, options)

    def test_same_num_options_different_prompt_types_differ(self):
        a = self._state(2, "Pick an available color: ")
        b = self._state(2, "Use a reroll? (y/n): ")
        assert a != b

    def test_same_prompt_different_option_colors_differ(self):
        blues = [Dice(DiceColor.BLUE) for _ in range(3)]
        for d in blues:
            d.set_value(3)
        greens = [Dice(DiceColor.GREEN) for _ in range(3)]
        for d in greens:
            d.set_value(3)
        a = self._state(3, "Pick a die index: ", blues)
        b = self._state(3, "Pick a die index: ", greens)
        assert a != b

    def test_same_prompt_same_colors_different_values_differ(self):
        low = [Dice(DiceColor.BLUE), Dice(DiceColor.BLUE), Dice(DiceColor.BLUE)]
        for i, d in enumerate(low):
            d.set_value(i + 1)
        high = [Dice(DiceColor.BLUE), Dice(DiceColor.BLUE), Dice(DiceColor.BLUE)]
        for i, d in enumerate(high):
            d.set_value(i + 4)
        a = self._state(3, "Pick a die index: ", low)
        b = self._state(3, "Pick a die index: ", high)
        assert a != b


class TestOptionBlockPadding:
    def test_short_options_zero_padded(self):
        observer = RLObserver(Board(), augmented=True)
        dice = [Dice(DiceColor.BLUE)]
        dice[0].set_value(2)
        state = observer.get_state(
            DecisionType.CHOOSE_INDEX, 1, "Pick a die index: ", dice,
        )
        tail = state[-OPTION_BLOCK_SIZE + OPTION_FEATURE_SIZE:]
        assert all(v == 0.0 for v in tail)

    def test_no_options_full_block_zero(self):
        observer = RLObserver(Board(), augmented=True)
        state = observer.get_state(DecisionType.CHOOSE_INDEX, 0, "Pick: ", None)
        option_block = state[-OPTION_BLOCK_SIZE:]
        assert all(v == 0.0 for v in option_block)
