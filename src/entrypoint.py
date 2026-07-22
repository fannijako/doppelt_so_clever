from __future__ import annotations

import argparse
from typing import Optional

from src.game.game import Game
from src.board.board import Board
from src.game.rl_observer import RLObserver
from src.game.game_observer import GameObserver
from src.actions.action_handler import ActionHandler
from src.game.logging_observer import LoggingObserver
from src.game.composite_observer import CompositeObserver
from src.logging_config import setup_logging, GameLogger
from src.input_handler.arcade_input_handler import ArcadeInputHandler
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler
from src.input_handler import (
    InputHandler,
    AutomaticInputHandler,
    ConsoleInputHandler,
    ModelInputHandler,
)

try:
    from src.ui.arcade_ui import ArcadeUI
    from src.ui.model_advisor import ModelAdvisor
except ImportError:
    ArcadeUI = None
    ModelAdvisor = None

from model.model import DoppeltSoCleverModel

logger = GameLogger(__name__)


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose)
    logger.info("Args", arguments)

    board = Board()
    observer, arcade_ui = build_observer(arguments, board)
    game = Game(
        board=board,
        observer=observer,
        input_handler=get_input_handler(arguments, arcade_ui),
        action_handler=ActionHandler(board=board),
    )

    if arguments.mode == "interactive":
        arcade_ui.run_with_game(game)
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


def build_observer(arguments: argparse.Namespace, board: Board) -> tuple[GameObserver, Optional[ArcadeUI]]:
    observers: list[GameObserver] = [LoggingObserver()]
    arcade_ui: Optional[ArcadeUI] = None

    if arguments.mode == "interactive":
        if ArcadeUI is None or ModelAdvisor is None:
            raise ImportError("interactive mode requires the interactive and rl extras: make build-interactive build-rl")
        augmented = ModelAdvisor.read_augmented_from_checkpoint()
        strategic_features = ModelAdvisor.read_strategic_features_from_checkpoint()
        rl_observer = RLObserver(board, augmented=augmented, strategic_features=strategic_features)
        advisor = ModelAdvisor(rl_observer)
        arcade_ui = ArcadeUI(board, model_advisor=advisor)
        observers.append(arcade_ui)
        observers.append(rl_observer)

    if len(observers) == 1:
        return observers[0], arcade_ui
    return CompositeObserver(observers), arcade_ui


def get_input_handler(arguments: argparse.Namespace, arcade_ui: Optional[ArcadeUI]) -> InputHandler:
    # pylint: disable=unnecessary-lambda
    handlers = {
        "console": lambda: ConsoleInputHandler(),
        "always-accept": lambda: AlwaysAcceptInputHandler(),
        "model": lambda: ModelInputHandler(DoppeltSoCleverModel()),
        "automatic": lambda: AutomaticInputHandler(),
        "interactive": lambda: ArcadeInputHandler(arcade_ui),  # type: ignore[arg-type]
    }

    handler_factory = handlers.get(arguments.mode)
    if handler_factory is None:
        raise ValueError(f"Unknown mode: {arguments.mode}")
    return handler_factory()


if __name__ == "__main__":
    main()
