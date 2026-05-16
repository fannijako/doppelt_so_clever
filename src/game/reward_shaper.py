from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.board.board import Board
    from src.game.rl_observer import RLObserver


@dataclass(frozen=True)
class RewardConfig:
    w_box: float = 0.5
    w_fox: float = 1.0
    w_resource: float = 0.5
    w_failed: float = 2.0
    w_score: float = 0.1
    use_partial_score: bool = False


@dataclass(frozen=True)
class BoardSnapshot:
    filled_boxes: int
    foxes: int
    gained_rerolls: int
    gained_plus_ones: int
    gained_reuses: int
    usable_rerolls: int
    usable_plus_ones: int
    usable_reuses: int
    failed_action_count: int
    partial_score: float | None = None

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
            usable_rerolls=board.usable_rerolls,
            usable_plus_ones=board.usable_plus_ones,
            usable_reuses=board.usable_reuses,
            failed_action_count=observer.failed_action_count,
            partial_score=board.partial_evaluate() if config.use_partial_score else None,
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
            + cfg.w_resource * _resource_delta(prev, curr)
            - cfg.w_failed * (curr.failed_action_count - prev.failed_action_count)
        )
        if cfg.use_partial_score and prev.partial_score is not None and curr.partial_score is not None:
            reward += cfg.w_score * (curr.partial_score - prev.partial_score)
        return reward


def _resource_delta(prev: BoardSnapshot, curr: BoardSnapshot) -> int:
    return (
        (curr.gained_rerolls - prev.gained_rerolls)
        + (curr.gained_plus_ones - prev.gained_plus_ones)
        + (curr.gained_reuses - prev.gained_reuses)
    )


def _count_filled_boxes(board: Board) -> int:
    blue = sum(1 for box in board.blue_board_part.boxes if box.value_used is not None)
    green = sum(1 for box in board.green_board_part.boxes if box.value_used is not None)
    pink = sum(1 for box in board.pink_board_part.boxes if box.value_used is not None)
    yellow = sum(
        1 for box in board.yellow_board_part.boxes if box.is_circled or box.is_crossed
    )
    grey = sum(1 for box in board.grey_board_part.boxes if box.is_crossed)
    return blue + green + pink + yellow + grey
