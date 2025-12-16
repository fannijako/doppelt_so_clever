import logging
import argparse

from src.pink_board_part import PinkBoardPart
from src.green_board_part import GreenBoardPart
from src.blue_board_part import BlueBoardPart
from src.dice import Dice, DiceColor


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
    pink_dice = Dice(DiceColor.PINK)
    pink_dice.roll()
    pink_board_part.add_dice(pink_dice)

    green_dice = Dice(DiceColor.GREEN)
    green_dice.roll()
    green_board_part.add_dice(green_dice)

    blue_dice = Dice(DiceColor.BLUE)
    blue_dice.roll()
    white_dice = Dice(DiceColor.WHITE)
    white_dice.roll()
    try:
        blue_board_part.add_dice(blue_dice, white_dice)
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
