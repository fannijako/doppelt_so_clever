import logging
import argparse

from src.active_round import ActiveRound
from src.board import Board


def main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments)
    logging.info(f"args: {arguments}")
    board = Board()
    board = ActiveRound(board).execute()
    logging.info(f"board value: {board.evaluate()}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def setup_logging(arguments: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.DEBUG if arguments.verbose else logging.INFO)


if __name__ == "__main__":
    main()
