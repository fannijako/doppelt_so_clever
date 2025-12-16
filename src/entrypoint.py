import logging
import argparse

from src.pink_board_part import PinkBoardPart
from src.green_board_part import GreenBoardPart
from src.blue_board_part import BlueBoardPart
from src.die import Die, DieColor


def main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments)
    logging.info("args: %s", arguments)
    pink_board_part = PinkBoardPart()
    green_board_part = GreenBoardPart()
    blue_board_part = BlueBoardPart()

    for _ in range(12):
        play_round(pink_board_part, green_board_part, blue_board_part)

    print(pink_board_part)
    print(f'Pink board part score: {pink_board_part.evaluate()}')
    print(green_board_part)
    print(f'Green board part score: {green_board_part.evaluate()}')
    print(blue_board_part)
    print(f'Blue board part score: {blue_board_part.evaluate()}')


def play_round(pink_board_part: PinkBoardPart, green_board_part: GreenBoardPart, blue_board_part: BlueBoardPart) -> None:
    pink_die = Die(DieColor.PINK)
    pink_die.roll()
    pink_board_part.add_die(pink_die)

    green_die = Die(DieColor.GREEN)
    green_die.roll()
    green_board_part.add_die(green_die)

    blue_die = Die(DieColor.BLUE)
    blue_die.roll()
    white_die = Die(DieColor.WHITE)
    white_die.roll()
    try:
        blue_board_part.add_die(blue_die, white_die)
    except ValueError as e:
        logging.warning(e)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def setup_logging(arguments: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.INFO if arguments.verbose else logging.WARNING)


if __name__ == "__main__":
    main()
