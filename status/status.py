from enum import Enum


class Status(Enum):
    SUCCESS = 0
    NO_CHOICE = -1
    NO_OFFERS = -2
    TRANSFER_INTERRUPTED = -3