from enum import Enum

class PacketType(Enum):
    DISCOVERY = 0
    OFFER = 1
    ACK = 2
    METADATA = 3