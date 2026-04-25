from src.dice.dice import Dice
from src.board.board import Board
from src.dice.dice_color import DiceColor
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.actions.immediate_actions.immediate_actions import ImmediateActions
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class BlueQuestionMarkAction(ImmediateActions):
    def __init__(self):
        super().__init__(action_type=ActionType.BLUE_QUESTION_MARK)

    def use(self, board: Board, automatic: bool) -> list[Action]:
        value_limit_on_next_box = board.blue_board_part.get_value_limit_on_next_box()
        logger.debug("Value limit", value_limit_on_next_box, "next blue box")

        blue_dice = Dice(DiceColor.BLUE)
        white_dice = Dice(DiceColor.WHITE)

        blue_dice.set_value(value_limit_on_next_box // 2)
        if value_limit_on_next_box % 2 == 0:
            white_dice.set_value(value_limit_on_next_box // 2)
        else:
            white_dice.set_value(value_limit_on_next_box // 2 + 1)

        logger.debug("Blue dice", blue_dice.value, "set")
        logger.debug("White dice", white_dice.value, "set")

        action = board.blue_board_part.add_dice(
            blue_dice,
            white_dice
        )
        return [action] if action else []
