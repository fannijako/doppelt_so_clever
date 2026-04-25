import logging
import os
from datetime import datetime


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(verbose: bool = False, log_to_file: bool = False, log_dir: str = "logs") -> None:
    level = logging.DEBUG if verbose else logging.INFO

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(
            filename=f"{log_dir}/game_{date_str}.log",
            mode="a",
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=handlers,
    )
