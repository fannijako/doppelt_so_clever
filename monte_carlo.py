import logging
import argparse
from datetime import datetime

import matplotlib.pyplot as plt

from src.game import Game
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose, log_to_file=True, log_dir="logs")
    logger.info(f"args: {arguments}")

    scores = run_simulation(arguments.rounds)

    plot_scores(
        scores,
        f"monte_carlo_scores/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
    )


def run_simulation(rounds: int) -> list[int]:
    scores = []
    for _ in range(rounds):
        game = Game(automatic=True)
        score = game.play()
        scores.append(score)

    logger.info(f"Scores: {scores}")

    return scores


def plot_scores(scores: list[int], filename: str) -> None:
    import os
    os.makedirs("monte_carlo_scores", exist_ok=True)

    plt.figure()
    plt.hist(scores, bins=20)
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.title("Histogram of Scores")
    plt.savefig(filename)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-r", "--rounds", type=int, default=1000, help="Number of rounds to play")
    return parser.parse_args()


if __name__ == "__main__":
    main()
