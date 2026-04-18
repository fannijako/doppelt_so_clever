import os
import logging
import argparse
from datetime import datetime

import matplotlib.pyplot as plt

from src.game import Game


def main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments)
    logging.info(f"args: {arguments}")

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

    logging.info(f"Scores: {scores}")

    return scores


def plot_scores(scores: list[int], filename: str) -> None:
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


def setup_logging(arguments: argparse.Namespace) -> None:
    os.makedirs("logs", exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    logging.basicConfig(
        level=logging.DEBUG if arguments.verbose else logging.INFO,
        filename=f"logs/monte_carlo_{date_str}.log",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


if __name__ == "__main__":
    main()
