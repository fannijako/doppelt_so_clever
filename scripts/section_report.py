from __future__ import annotations

import argparse
import logging
import statistics
from collections import Counter
from dataclasses import dataclass

from scripts.evaluate_rl import _create_policy_fn, _load_policy
from scripts.train_rl import assert_observer_state_size
from src.actions.action_handler import ActionHandler
from src.board.board import Board
from src.game.game import Game
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler

logger = logging.getLogger(__name__)

SECTION_NAMES = ("blue", "pink", "green", "yellow", "grey")
SCORE_THRESHOLDS = (140, 160, 180)


@dataclass(frozen=True)
class GameStats:
    total: int
    sections: tuple[int, ...]
    foxes: int

    @property
    def min_section_index(self) -> int:
        return self.sections.index(min(self.sections))

    @property
    def fox_bonus(self) -> int:
        return self.foxes * min(self.sections)


def main() -> None:
    args = _parse_arguments()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    policy, augmented, strategic_features = _load_policy(args.checkpoint)
    policy_fn = _create_policy_fn(policy)
    expected_state_size = policy.trunk[0].in_features
    logger.info("Playing %d argmax games with %s", args.num_games, args.checkpoint)
    stats = [
        _play_game(policy_fn, augmented, strategic_features, expected_state_size)
        for _ in range(args.num_games)
    ]
    print(format_report(stats))


def _play_game(
    policy_fn, augmented: bool, strategic_features: bool, expected_state_size: int,
) -> GameStats:
    board = Board()
    observer = RLObserver(board, augmented=augmented, strategic_features=strategic_features)
    assert_observer_state_size(observer, expected_state_size)
    handler = RLInputHandler(observer, policy_fn, training=False)
    game = Game(
        input_handler=handler,
        board=board,
        observer=observer,
        action_handler=ActionHandler(board=board),
    )
    total = game.play()
    sections = (
        board.blue_board_part.evaluate(),
        board.pink_board_part.evaluate(),
        board.green_board_part.evaluate(),
        board.yellow_board_part.evaluate(),
        board.grey_board_part.evaluate(),
    )
    return GameStats(total=total, sections=sections, foxes=board.foxes)


def format_report(stats: list[GameStats]) -> str:
    return "\n".join(
        _total_lines(stats)
        + _section_lines(stats)
        + _min_section_lines(stats)
        + _fox_lines(stats)
        + _threshold_lines(stats)
    )


def _total_lines(stats: list[GameStats]) -> list[str]:
    totals = [s.total for s in stats]
    return [
        f"TOTAL  mean={statistics.mean(totals):.1f}  median={statistics.median(totals):.0f}"
        f"  max={max(totals)}  std={statistics.pstdev(totals):.1f}  n={len(stats)}"
    ]


def _section_lines(stats: list[GameStats]) -> list[str]:
    return [
        f"  {name:<7} {statistics.mean(s.sections[i] for s in stats):>6.1f}"
        for i, name in enumerate(SECTION_NAMES)
    ]


def _min_section_lines(stats: list[GameStats]) -> list[str]:
    counts = Counter(SECTION_NAMES[s.min_section_index] for s in stats)
    shares = "  ".join(
        f"{name} {100.0 * counts[name] / len(stats):.1f}%"
        for name in SECTION_NAMES if counts[name]
    )
    return [f"min section: {shares}"]


def _fox_lines(stats: list[GameStats]) -> list[str]:
    foxes_per_game = statistics.mean(s.foxes for s in stats)
    total_points = sum(s.total for s in stats)
    fox_share = 100.0 * sum(s.fox_bonus for s in stats) / total_points if total_points else 0.0
    return [f"foxes/game={foxes_per_game:.2f}  fox bonus={fox_share:.1f}% of total"]


def _threshold_lines(stats: list[GameStats]) -> list[str]:
    shares = "  ".join(
        f">={t}: {100.0 * sum(1 for s in stats if s.total >= t) / len(stats):.1f}%"
        for t in SCORE_THRESHOLDS
    )
    return [shares]


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Per-section evaluation report for an RL checkpoint")
    parser.add_argument("--checkpoint", type=str, required=True, help="RL checkpoint path")
    parser.add_argument("-n", "--num-games", type=int, default=300, help="Argmax games to play")
    return parser.parse_args()


if __name__ == "__main__":
    main()
