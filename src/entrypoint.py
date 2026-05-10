import argparse
from typing import Optional

from src.game.game import Game
from src.board.board import Board
from src.ui.pygame_ui import PygameUI
from src.game.rl_observer import RLObserver
from src.ui.model_advisor import ModelAdvisor
from src.game.game_observer import GameObserver
from src.actions.action_handler import ActionHandler
from src.game.logging_observer import LoggingObserver
from src.game.composite_observer import CompositeObserver
from src.logging_config import setup_logging, GameLogger
from src.input_handler.pygame_input_handler import PygameInputHandler
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler
from src.input_handler import (
    InputHandler,
    AutomaticInputHandler,
    ConsoleInputHandler,
    ModelInputHandler,
)

from model.model import DoppeltSoCleverModel

logger = GameLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose)
    logger.info("Args", arguments)

    board = Board()
    observer, pygame_ui = build_observer(arguments, board)
    game = Game(
        board=board,
        observer=observer,
        input_handler=get_input_handler(arguments, pygame_ui),
        action_handler=ActionHandler(board=board),
    )

    if arguments.mode == "interactive":
        pygame_ui.run_with_game(game)
    else:
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


def build_observer(arguments: argparse.Namespace, board: Board) -> tuple[GameObserver, Optional[PygameUI]]:
    observers: list[GameObserver] = [LoggingObserver()]
    pygame_ui: Optional[PygameUI] = None

    if arguments.mode == "interactive":
        rl_observer = RLObserver(board)
        advisor = ModelAdvisor(rl_observer)
        pygame_ui = PygameUI(board, model_advisor=advisor)
        observers.append(pygame_ui)
        observers.append(rl_observer)

    if len(observers) == 1:
        return observers[0], pygame_ui
    return CompositeObserver(observers), pygame_ui


def get_input_handler(arguments: argparse.Namespace, pygame_ui: Optional[PygameUI]) -> InputHandler:
    # pylint: disable=unnecessary-lambda
    handlers = {
        "console": lambda: ConsoleInputHandler(),
        "always-accept": lambda: AlwaysAcceptInputHandler(),
        "model": lambda: ModelInputHandler(DoppeltSoCleverModel()),
        "automatic": lambda: AutomaticInputHandler(),
        "interactive": lambda: PygameInputHandler(pygame_ui),  # type: ignore[arg-type]
    }

    handler_factory = handlers.get(arguments.mode)
    if handler_factory is None:
        raise ValueError(f"Unknown mode: {arguments.mode}")
    return handler_factory()


if __name__ == "__main__":
    main()
