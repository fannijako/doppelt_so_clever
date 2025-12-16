import logging

from src.actions import Action
from src.blue_box import BlueBox
from src.die import Die, DieColor


class BlueBoardPart:
    def __init__(self) -> None:
        logging.debug("Initializing a blue board part")
        self.boxes: list[BlueBox] = [
            BlueBox(12, Action.NONE),
            BlueBox(12, Action.REUSE),
            BlueBox(12, Action.YELLOW_QUESTION_MARK),
            BlueBox(12, Action.NONE),
            BlueBox(12, Action.PLUS_ONE),
            BlueBox(12, Action.REROLL),
            BlueBox(12, Action.PINK_QUESTION_MARK),
            BlueBox(12, Action.NONE),
            BlueBox(12, Action.FOX),
            BlueBox(12, Action.REUSE),
            BlueBox(12, Action.NONE),
            BlueBox(12, Action.GREEN_QUESTION_MARK),
        ]

    def add_die(self, blue_die: Die, white_die: Die) -> Action:
        self._validate_die(blue_die, white_die)
        logging.info(f'Adding die {str(blue_die)} to blue board part with {str(white_die)}')

        for index, current_blue_box in enumerate(self.boxes):
            if current_blue_box.value_used is None:
                current_blue_box.add_die_value(blue_die.value, white_die.value)
                logging.info(f'Added die {str(blue_die)} to blue box {index}')

                for following_box in self.boxes[index + 1:]:
                    following_box.maximum_value_limit = current_blue_box.value_used
                logging.info(f'Lowered following boxes upper limits to {current_blue_box.value_used}')

                return current_blue_box.action

        raise ValueError("No free blue box available to add die")

    @staticmethod
    def _validate_die(blue_die: Die, white_die: Die) -> None:
        if blue_die.color != DieColor.BLUE or white_die.color != DieColor.WHITE:
            message = "Attempted to add a die of a different color to blue board part"
            logging.warning(message)
            raise ValueError(message)

        if blue_die.value is None or white_die.value is None:
            message = "Attempted to add an unrolled die to blue board part"
            logging.warning(message)
            raise ValueError(message)

    def __str__(self) -> str:
        return '\n'.join([str(box) for box in self.boxes])

    def evaluate(self) -> int:
        point_die_number_map = {
            0: 0,
            1: 1,
            2: 3,
            3: 6,
            4: 10,
            5: 15,
            6: 21,
            7: 28,
            8: 36,
            9: 45,
            10: 55,
            11: 66,
            12: 78,
        }
        number_of_boxes_used = len([box for box in self.boxes if box.value_used is not None])
        return point_die_number_map.get(number_of_boxes_used, 0)
