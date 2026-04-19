import logging
import argparse

from src.game import Game
from src.pygame_game import PygameGame


def main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments)
    logging.info(f"args: {arguments}")

    if arguments.pygame:
        game = PygameGame()
    else:
        game = Game(automatic=arguments.automatic)

    game.play()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-a", "--automatic", action="store_true", help="Enable automatic play")
    parser.add_argument("-p", "--pygame", action="store_true", help="Enable pygame UI")
    return parser.parse_args()


def setup_logging(arguments: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.DEBUG if arguments.verbose else logging.INFO)


if __name__ == "__main__":
    main()
