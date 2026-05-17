from __future__ import annotations

from typing import Any

from src.dice.dice import Dice
from src.dice.dice_color import DiceColor
from src.actions.base_action import Action
from src.actions.action_type import ActionType
from src.board.board_parts.yellow_board_part import YellowBoardAction


OPTION_FEATURE_SIZE = 12
MAX_OPTIONS = 30
OPTION_BLOCK_SIZE = MAX_OPTIONS * OPTION_FEATURE_SIZE


_COLOR_INDEX: dict[DiceColor, int] = {c: i for i, c in enumerate(DiceColor)}
_COLOR_BY_VALUE: dict[str, DiceColor] = {c.value: c for c in DiceColor}


_ACTION_BUCKETS: dict[ActionType, int] = {
    ActionType.NONE: 0,
    ActionType.REROLL: 1,
    ActionType.REUSE: 1,
    ActionType.PLUS_ONE: 1,
    ActionType.BLACK_QUESTION_MARK: 2,
    ActionType.BLUE_QUESTION_MARK: 3,
    ActionType.GREEN_QUESTION_MARK: 3,
    ActionType.YELLOW_QUESTION_MARK: 3,
    ActionType.GREY_QUESTION_MARK: 3,
    ActionType.PINK_QUESTION_MARK: 3,
    ActionType.FOX: 4,
}
_ACTION_BUCKET_COUNT = 5


def featurize_options(options: list[Any] | None) -> list[list[float]]:
    if not options:
        return []
    return [
        _featurize_option(option, index)
        for index, option in enumerate(options[:MAX_OPTIONS])
    ]


def flatten_option_block(featurized: list[list[float]]) -> list[float]:
    block = [0.0] * OPTION_BLOCK_SIZE
    for i, row in enumerate(featurized):
        start = i * OPTION_FEATURE_SIZE
        block[start:start + OPTION_FEATURE_SIZE] = row
    return block


def _featurize_option(option: Any, index: int) -> list[float]:
    feature = [0.0] * OPTION_FEATURE_SIZE
    feature[0] = index / MAX_OPTIONS
    _encode_option(feature, option)
    return feature


def _encode_option(feature: list[float], option: Any) -> None:
    if isinstance(option, Dice):
        _encode_dice(feature, option)
        return
    if isinstance(option, Action):
        _encode_action(feature, option)
        return
    if isinstance(option, YellowBoardAction):
        _encode_yellow_action(feature, option)
        return
    if isinstance(option, tuple):
        _encode_tuple(feature, option)
        return
    if isinstance(option, str):
        _encode_color_string(feature, option)


def _encode_dice(feature: list[float], dice: Dice) -> None:
    _set_color(feature, dice.color)
    if dice.value is not None:
        feature[7] = dice.value / 6.0


def _encode_action(feature: list[float], action: Action) -> None:
    bucket = _ACTION_BUCKETS.get(action.action_type, 0)
    feature[11] = bucket / _ACTION_BUCKET_COUNT


def _encode_yellow_action(feature: list[float], action: YellowBoardAction) -> None:
    feature[10] = 1.0 if action == YellowBoardAction.CIRCLE else 0.0


def _encode_tuple(feature: list[float], option: tuple) -> None:
    if len(option) == 2 and isinstance(option[0], DiceColor):
        _set_color(feature, option[0])
        feature[7] = option[1] / 6.0
        return
    if len(option) == 3 and isinstance(option[2], YellowBoardAction):
        feature[8] = option[0] / 4.0
        feature[9] = option[1] / 6.0
        feature[10] = 1.0 if option[2] == YellowBoardAction.CIRCLE else 0.0
        return
    if len(option) == 4 and isinstance(option[3], YellowBoardAction):
        feature[7] = option[0] / 6.0
        feature[8] = option[1] / 4.0
        feature[9] = option[2] / 6.0
        feature[10] = 1.0 if option[3] == YellowBoardAction.CIRCLE else 0.0


def _encode_color_string(feature: list[float], option: str) -> None:
    color = _COLOR_BY_VALUE.get(option.lower())
    if color is not None:
        _set_color(feature, color)


def _set_color(feature: list[float], color: DiceColor) -> None:
    feature[1 + _COLOR_INDEX[color]] = 1.0
