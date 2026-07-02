from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.board.board import Board
    from src.game.rl_observer import RLObserver


@dataclass(frozen=True)
class RewardConfig:  # pylint: disable=too-many-instance-attributes
    w_box: float = 0.25
    w_fox: float = 0.25
    w_plus_one: float = 0.5
    w_reroll: float = 0.15
    w_reuse: float = 0.15
    w_consumed_immediate: float = 0.5
    w_failed: float = 1.0
    w_score: float = 0.1
    use_partial_score: bool = False
    w_min_section: float = 0.0


NO_SHAPING_REWARD_CONFIG = RewardConfig(
    w_box=0.0, w_fox=0.0, w_plus_one=0.0, w_reroll=0.0, w_reuse=0.0,
    w_consumed_immediate=0.0, w_failed=0.0, w_score=0.0,
    use_partial_score=False,
)

MIN_SECTION_PBRS_REWARD_CONFIG = RewardConfig(
    w_box=0.0, w_fox=0.0, w_plus_one=0.0, w_reroll=0.0, w_reuse=0.0,
    w_consumed_immediate=0.0, w_failed=0.0, w_score=0.0,
    use_partial_score=False, w_min_section=0.1,
)

REWARD_MODE_CONFIGS = {
    "none": NO_SHAPING_REWARD_CONFIG,
    "total": RewardConfig(),
    "min-section": MIN_SECTION_PBRS_REWARD_CONFIG,
}


@dataclass(frozen=True)
class BoardSnapshot:  # pylint: disable=too-many-instance-attributes
    filled_boxes: int
    foxes: int
    gained_rerolls: int
    gained_plus_ones: int
    gained_reuses: int
    consumed_immediate_actions: int
    failed_action_count: int
    partial_score: float | None = None
    min_section_score: int | None = None

    @classmethod
    def capture(
        cls, board: Board, observer: RLObserver, config: RewardConfig,
    ) -> BoardSnapshot:
        return cls(
            filled_boxes=_count_filled_boxes(board),
            foxes=board.foxes,
            gained_rerolls=board.gained_rerolls,
            gained_plus_ones=board.gained_plus_ones,
            gained_reuses=board.gained_reuses,
            consumed_immediate_actions=board.consumed_immediate_actions,
            failed_action_count=observer.failed_action_count,
            partial_score=board.partial_evaluate() if config.use_partial_score else None,
            min_section_score=board.min_section_score() if config.w_min_section else None,
        )


class RewardShaper:
    def __init__(self, config: RewardConfig | None = None):
        self._config = config or RewardConfig()

    @property
    def config(self) -> RewardConfig:
        return self._config

    def compute(self, prev: BoardSnapshot, curr: BoardSnapshot) -> float:
        cfg = self._config
        reward = (
            cfg.w_box * (curr.filled_boxes - prev.filled_boxes)
            + cfg.w_fox * (curr.foxes - prev.foxes)
            + cfg.w_plus_one * (curr.gained_plus_ones - prev.gained_plus_ones)
            + cfg.w_reroll * (curr.gained_rerolls - prev.gained_rerolls)
            + cfg.w_reuse * (curr.gained_reuses - prev.gained_reuses)
            + cfg.w_consumed_immediate * (curr.consumed_immediate_actions - prev.consumed_immediate_actions)
            - cfg.w_failed * (curr.failed_action_count - prev.failed_action_count)
        )
        if cfg.use_partial_score and prev.partial_score is not None and curr.partial_score is not None:
            reward += cfg.w_score * (curr.partial_score - prev.partial_score)
        if prev.min_section_score is not None and curr.min_section_score is not None:
            reward += cfg.w_min_section * (curr.min_section_score - prev.min_section_score)
        return reward


def _count_filled_boxes(board: Board) -> int:
    blue = sum(1 for box in board.blue_board_part.boxes if box.value_used is not None)
    green = sum(1 for box in board.green_board_part.boxes if box.value_used is not None)
    pink = sum(1 for box in board.pink_board_part.boxes if box.value_used is not None)
    yellow = sum(
        1 for box in board.yellow_board_part.boxes if box.is_circled or box.is_crossed
    )
    grey = sum(1 for box in board.grey_board_part.boxes if box.is_crossed)
    return blue + green + pink + yellow + grey
