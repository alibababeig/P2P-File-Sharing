FILENAME_LENGTH_BYTES = 2
ENDIANNESS = 'little'


class Discovery:
    def __init__(self):
        self.filename = None
        self.bytes = None

    def get_filename(self):
        return self.filename

    def set_filename(self, filename):
        self.filename = filename
        filename_length = len(filename.encode('utf-8'))
        self.bytes = filename_length.to_bytes(
            FILENAME_LENGTH_BYTES, ENDIANNESS) + filename.encode('utf-8')

    def get_bytes(self):
        return self.bytes

    def set_bytes(self, _bytes):
        self.bytes = _bytes
        filename_length = int.from_bytes(
            _bytes[:FILENAME_LENGTH_BYTES], ENDIANNESS)
        if len(_bytes) != FILENAME_LENGTH_BYTES + filename_length:
            raise ValueError()
        self.filename = _bytes[FILENAME_LENGTH_BYTES:].decode('utf-8')
