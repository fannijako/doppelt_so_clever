import logging
import argparse


def main() -> None:
    arguments = parse_arguments()
    setup_logging(arguments)
    logging.info("args: %s", arguments)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def setup_logging(arguments: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.INFO if arguments.verbose else logging.WARNING)


if __name__ == "__main__":
    main()
