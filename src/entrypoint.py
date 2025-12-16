import logging
import argparse

from src.pink_board_part import PinkBoardPart
from src.die import Die, DieColor


def main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments)
    logging.info("args: %s", arguments)
    pink_board_part = PinkBoardPart()

    for _ in range(10):
        play_round(pink_board_part)

    print([str(box) for box in pink_board_part.boxes])


def play_round(pink_board_part: PinkBoardPart) -> None:
    die = Die(DieColor.PINK)
    die.roll()
    pink_board_part.add_die(die)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def setup_logging(arguments: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.INFO if arguments.verbose else logging.WARNING)


if __name__ == "__main__":
    main()
