import os
import logging
import argparse
from datetime import datetime

import matplotlib.pyplot as plt

from src.game import Game
from src.logging_config import setup_logging
from src.input_handler import InputHandler, AutomaticInputHandler
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler

logger = logging.getLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose, log_to_file=True, log_dir="logs")
    logger.info(f"args: {arguments}")

    input_handler = get_input_handler(arguments)
    scores = run_simulation(arguments.rounds, input_handler)

    plot_scores(
        scores,
        f"monte_carlo_scores/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
    )


def run_simulation(rounds: int, input_handler: InputHandler) -> list[int]:
    scores = []
    for _ in range(rounds):
        game = Game(input_handler=input_handler)
        score = game.play()
        scores.append(score)

    logger.info(f"Scores: {scores}")

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
    parser.add_argument("--always-accept", action="store_true", help="Use always-accept heuristic for automatic play")
    return parser.parse_args()


def get_input_handler(arguments: argparse.Namespace) -> InputHandler:
    if arguments.always_accept:
        return AlwaysAcceptInputHandler()
    return AutomaticInputHandler()


if __name__ == "__main__":
    main()
