from src.game.rl_observer import (
    PromptType,
    classify_prompt,
    _prompt_type_one_hot,
    PROMPT_FEATURES_SIZE,
)


class TestClassifyPrompt:
    def test_pick_available_color(self):
        assert classify_prompt("Pick an available color: ") == PromptType.PICK_DIE_COLOR

    def test_place_die(self):
        assert classify_prompt("Place die Dice(BLUE, 3)? (y/n): ") == PromptType.PLACE_DIE

    def test_use_reroll(self):
        assert classify_prompt("Use a reroll? (y/n): ") == PromptType.USE_REROLL

    def test_use_reuse(self):
        assert classify_prompt("Use a reuse? (y/n): ") == PromptType.USE_REUSE

    def test_use_plus_one(self):
        assert classify_prompt("Use a plus one? (y/n): ") == PromptType.USE_PLUS_ONE

    def test_pick_action_to_use(self):
        assert classify_prompt("Add the index of the action to use: ") == PromptType.PICK_ACTION

    def test_select_placement(self):
        assert classify_prompt("Select a placement: ") == PromptType.PICK_PLACEMENT

    def test_pick_die_index(self):
        assert classify_prompt("Pick a die index: ") == PromptType.PICK_DIE_INDEX

    def test_substitute_white(self):
        assert classify_prompt("Pick an available color to play white as: ") == PromptType.PICK_COLOR_SUBSTITUTE

    def test_substitute_grey(self):
        assert classify_prompt("Pick an available color to substitute grey as: ") == PromptType.PICK_COLOR_SUBSTITUTE

    def test_enter_color(self):
        assert classify_prompt("Enter a color: ") == PromptType.PICK_COLOR_QUESTION_MARK

    def test_unknown_prompt(self):
        assert classify_prompt("something unexpected") == PromptType.UNKNOWN

    def test_die_color_to_reuse(self):
        assert classify_prompt("Pick a die color to reuse: ") == PromptType.PICK_DIE_COLOR


class TestPromptTypeOneHot:
    def test_length(self):
        assert len(_prompt_type_one_hot(PromptType.PLACE_DIE)) == PROMPT_FEATURES_SIZE

    def test_sums_to_one(self):
        assert sum(_prompt_type_one_hot(PromptType.USE_REROLL)) == 1.0

    def test_correct_index_set(self):
        one_hot = _prompt_type_one_hot(PromptType.PICK_ACTION)
        assert one_hot[PromptType.PICK_ACTION.value] == 1.0
