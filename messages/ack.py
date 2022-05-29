FILENAME_LENGTH_BYTES = 2
PORT_NUMBER_BYTES = 2
ENDIANNESS = 'little'


class Ack:
    def __init__(self):
        self.data = None
        self.bytes = None

    def get_filename(self):
        return self.data[0]

    def get_port_number(self):
        return self.data[1]

    def set_data(self, filename, port_number):
        self.data = (filename, port_number)

        filename_length = len(filename.encode('utf-8'))
        _bytes = filename_length.to_bytes(FILENAME_LENGTH_BYTES, ENDIANNESS)
        _bytes += filename.encode('utf-8')
        _bytes += port_number.to_bytes(PORT_NUMBER_BYTES, ENDIANNESS)

        self.bytes = _bytes

    def get_bytes(self):
        return self.bytes

    def set_bytes(self, _bytes):
        self.bytes = _bytes

        if len(_bytes) < FILENAME_LENGTH_BYTES:
            raise ValueError()

        filename_length = int.from_bytes(
            _bytes[:FILENAME_LENGTH_BYTES], ENDIANNESS)
        if len(_bytes) != FILENAME_LENGTH_BYTES + filename_length + PORT_NUMBER_BYTES:
            raise ValueError()

        filename = _bytes[FILENAME_LENGTH_BYTES:
                          FILENAME_LENGTH_BYTES + filename_length].decode('utf-8')

        port_number = int.from_bytes(
            _bytes[FILENAME_LENGTH_BYTES + filename_length:], ENDIANNESS)

        self.data = (filename, port_number)
