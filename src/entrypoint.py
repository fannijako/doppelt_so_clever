import argparse

from src.game.game import Game
from src.board.board import Board
from src.ui.pygame_ui import PygameUI
from src.game.pygame_game import PygameGame
from src.actions.action_handler import ActionHandler
from src.game.logging_observer import LoggingObserver
from src.logging_config import setup_logging, GameLogger
from src.input_handler.pygame_input_handler import PygameInputHandler
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler
from src.input_handler import InputHandler, AutomaticInputHandler, ConsoleInputHandler, ModelInputHandler

from model.model import DoppeltSoCleverModel

logger = GameLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose)
    logger.info("Args", arguments)

    board = Board()

    if arguments.mode == 'interactive':
        game = PygameGame(
            board=board,
            observer=PygameUI(board),
            input_handler=PygameInputHandler(),
            action_handler=ActionHandler(board=board),
        )
    else:
        game = Game(
            input_handler=get_action_handler(arguments),
            board=board,
            observer=LoggingObserver(),
            action_handler=ActionHandler(board=board),
        )

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
