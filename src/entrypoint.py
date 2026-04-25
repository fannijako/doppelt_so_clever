import argparse

from src.game import Game
from src.logging_config import setup_logging, GameLogger
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler
from src.input_handler import InputHandler, AutomaticInputHandler, ConsoleInputHandler

logger = GameLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose)
    logger.info("Args", arguments)
    game = Game(input_handler=get_action_handler(arguments))
    game.play()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-a", "--automatic", action="store_true", help="Enable automatic play")
    parser.add_argument("--always-accept", action="store_true", help="Use always-accept heuristic for automatic play")
    return parser.parse_args()


def get_action_handler(arguments: argparse.Namespace) -> InputHandler:
    if not arguments.automatic:
        return ConsoleInputHandler()
    if arguments.always_accept:
        return AlwaysAcceptInputHandler()
    return AutomaticInputHandler()


if __name__ == "__main__":
    main()
