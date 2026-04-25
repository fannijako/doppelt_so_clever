import logging
import argparse

from src.game import Game
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose)
    logger.info(f"args: {arguments}")
    game = Game(automatic=arguments.automatic)
    game.play()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-a", "--automatic", action="store_true", help="Enable automatic play")
    return parser.parse_args()


if __name__ == "__main__":
    main()
