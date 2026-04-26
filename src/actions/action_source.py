from enum import Enum


class ActionSource(Enum):
    ROUND_START = "round_start"
    PICK = "pick"
    PLUS_ONE = "plus_one"
    PASSIVE_PICK = "passive_pick"
