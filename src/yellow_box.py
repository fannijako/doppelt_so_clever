import logging

from src.actions import Action


class YellowBox:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        value: int,
        row_position: int,
        column_position: int,
        row_action: Action,
        column_action: Action
    ) -> None:
        logging.debug("Initializing a yellow box")
        self._validate_input(value, row_position, column_position)
        self.value = value
        self.row_position = row_position
        self.column_position = column_position
        self.row_action = row_action
        self.column_action = column_action
        self.is_circled = False
        self.is_crossed = False

    def circle_box(self) -> None:
        if self.is_circled:
            raise ValueError('Box is already circled')
        self.is_circled = True

    def cross_box(self) -> None:
        if self.is_crossed:
            raise ValueError('Box is already crossed')
        if not self.is_circled:
            raise ValueError('Box must be circled before it can be crossed')
        self.is_crossed = True

    def __str__(self) -> str:
        return f"Yellow box: {self.value}"

    @staticmethod
    def _validate_input(value: int, row_position: int, column_position: int) -> None:
        if not 1 <= value <= 6:
            message = "value must be between 1 and 6"
            logging.error(message)
            raise ValueError(message)

        if not 0 <= row_position <= 4:
            message = "row_position must be between 0 and 4"
            logging.error(message)
            raise ValueError(message)

        if not 0 <= column_position <= 3:
            message = "column_position must be between 0 and 3"
            logging.error(message)
            raise ValueError(message)

        logging.debug("Valid input")
