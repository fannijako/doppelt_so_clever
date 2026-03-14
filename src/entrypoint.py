import logging
import argparse

from src.game import Game


def main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments)
    logging.info(f"args: {arguments}")
    game = Game(automatic=arguments.automatic)
    game.play()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-a", "--automatic", action="store_true", help="Enable automatic play")
    return parser.parse_args()


def setup_logging(arguments: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.DEBUG if arguments.verbose else logging.INFO)


if __name__ == "__main__":
    main()
