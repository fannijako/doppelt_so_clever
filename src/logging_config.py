import logging
import os
import sys
from datetime import datetime


SEPARATOR = " | "
COL_WIDTHS = {"levelname": 5, "location": 27, "category": 20}


class _TabularFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        record.asctime = self.formatTime(record, self.datefmt)
        class_name = getattr(record, "className", record.module)
        location = f"{class_name}.{record.funcName}"

        category = getattr(record, "category", "")
        value = getattr(record, "value", "")
        comment = getattr(record, "comment", "")

        if category:
            message = category.ljust(COL_WIDTHS["category"])
            str_value = str(value)
            if str_value:
                message += ": " + str_value
            if comment:
                message += " - " + comment
        else:
            message = record.getMessage()

        columns = [
            record.asctime,
            record.levelname.ljust(COL_WIDTHS["levelname"]),
            location.ljust(COL_WIDTHS["location"]),
            message,
        ]
        return SEPARATOR.join(columns)


class _ClassNameFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    def filter(self, record: logging.LogRecord) -> bool:
        frame = sys._getframe()  # pylint: disable=protected-access
        while frame is not None:
            if frame.f_code.co_filename not in (logging.__file__, __file__):
                instance = frame.f_locals.get("self")
                if instance is not None:
                    record.className = type(instance).__name__
                    return True
                cls = frame.f_locals.get("cls")
                if cls is not None:
                    record.className = cls.__name__
                    return True
                record.className = record.module
                return True
            frame = frame.f_back
        record.className = record.module
        return True


class GameLogger:
    """Structured logger with (category, value, comment) API."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def _log(self, level: int, category: str, value: object, comment: str) -> None:
        self._logger.log(level, "", extra={"category": category, "value": value, "comment": comment}, stacklevel=3)

    def info(self, category: str, value: object = "", comment: str = "") -> None:
        self._log(logging.INFO, category, value, comment)

    def debug(self, category: str, value: object = "", comment: str = "") -> None:
        self._log(logging.DEBUG, category, value, comment)

    def warning(self, category: str, value: object = "", comment: str = "") -> None:
        self._log(logging.WARNING, category, value, comment)

    def error(self, category: str, value: object = "", comment: str = "") -> None:
        self._log(logging.ERROR, category, value, comment)


def setup_logging(verbose: bool = False, log_to_file: bool = False, log_dir: str = "logs") -> None:
    level = logging.DEBUG if verbose else logging.INFO

    class_filter = _ClassNameFilter()

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(
            filename=f"{log_dir}/game_{date_str}.log",
            mode="a",
        )
        handlers.append(file_handler)

    formatter = _TabularFormatter()

    logging.basicConfig(
        level=level,
        handlers=handlers,
    )

    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
        handler.addFilter(class_filter)
