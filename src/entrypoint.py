import argparse

from src.game.game import Game
from src.game.pygame_game import PygameGame
from src.logging_config import setup_logging, GameLogger
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler
from src.input_handler import InputHandler, AutomaticInputHandler, ConsoleInputHandler, ModelInputHandler
from model.model import DoppeltSoCleverModel

logger = GameLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose)
    logger.info("Args", arguments)
    game = PygameGame() if arguments.mode == 'interactive' else Game(input_handler=get_action_handler(arguments))
    game.play()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--mode",
        choices=["console", "automatic", "always-accept", "model", "interactive"],
        default="console",
        help="Input mode: console (default), automatic, always-accept, model, or interactive"
    )
    return parser.parse_args()


def get_action_handler(arguments: argparse.Namespace) -> InputHandler:
    # pylint: disable=unnecessary-lambda
    handlers = {
        "console": lambda: ConsoleInputHandler(),
        "always-accept": lambda: AlwaysAcceptInputHandler(),
        "model": lambda: ModelInputHandler(DoppeltSoCleverModel()),
        "automatic": lambda: AutomaticInputHandler(),
    }

    handler_factory = handlers.get(arguments.mode)
    if handler_factory is None:
        raise ValueError(f"Unknown mode: {arguments.mode}")
    return handler_factory()


if __name__ == "__main__":
    main()
