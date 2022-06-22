FILENAME_LENGTH_BYTES = 2
HOST_ID_LEN_BYTES = 4
ENDIANNESS = 'little'


class Discovery:
    def __init__(self):
        self.bytes = None
        self.filename = None
        self.__src_host_id = None
        self.__dst_host_id = None

    def get_filename(self):
        return self.filename

    def get_src_host_id(self):
        return self.__src_host_id

    def get_dst_host_id(self):
        return self.__dst_host_id

    # src_addr and dst_addr must be exactly 32 bits long
    def set_filename(self, filename, src_host_id, dst_host_id):
        self.filename = filename
        self.__src_host_id = src_host_id
        self.__dst_host_id = dst_host_id

        # self.bytes = bytes(map(int, src_addr.split('.')))
        # self.bytes += bytes(map(int, dst_addr.split('.')))
        self.bytes = src_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        self.bytes += dst_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)

        filename_length = len(filename.encode('utf-8'))
        self.bytes += filename_length.to_bytes(
            FILENAME_LENGTH_BYTES, ENDIANNESS)
        self.bytes += filename.encode('utf-8')

    def get_bytes(self):
        return self.bytes

    def set_bytes(self, _bytes):
        self.bytes = _bytes
        if len(_bytes) < FILENAME_LENGTH_BYTES:
            raise ValueError()

        cursor = 0
        # self.src_addr = ''
        # for i in range(HOST_ID_LEN_BYTES):
        #     self.src_addr += str(int.from_bytes(self.bytes[cursor:cursor+1], ENDIANNESS)) + ('' if i == HOST_ID_LEN_BYTES-1 else '.')
        #     cursor += 1
        # self.dst_addr = ''
        # for i in range(HOST_ID_LEN_BYTES):
        #     self.dst_addr += str(int.from_bytes(self.bytes[cursor:cursor+1], ENDIANNESS)) + ('' if i == HOST_ID_LEN_BYTES-1 else '.')
        #     cursor += 1
        self.__src_host_id = int.from_bytes(
            self.bytes[cursor:cursor+HOST_ID_LEN_BYTES], ENDIANNESS)
        cursor += HOST_ID_LEN_BYTES
        self.__dst_host_id = int.from_bytes(
            self.bytes[cursor:cursor+HOST_ID_LEN_BYTES], ENDIANNESS)
        cursor += HOST_ID_LEN_BYTES

        filename_length = int.from_bytes(
            self.bytes[cursor:cursor+FILENAME_LENGTH_BYTES], ENDIANNESS)
        cursor += FILENAME_LENGTH_BYTES

        if len(self.bytes) != 2*HOST_ID_LEN_BYTES + FILENAME_LENGTH_BYTES + filename_length:
            raise ValueError()

        self.filename = self.bytes[cursor:].decode('utf-8')
