import argparse

from src.game import Game
from src.logging_config import setup_logging, GameLogger
from src.input_handler import AutomaticInputHandler, ConsoleInputHandler

logger = GameLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose)
    logger.info("Args", arguments)
    input_handler = AutomaticInputHandler() if arguments.automatic else ConsoleInputHandler()
    game = Game(input_handler=input_handler)
    game.play()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-a", "--automatic", action="store_true", help="Enable automatic play")
    return parser.parse_args()


if __name__ == "__main__":
    main()
