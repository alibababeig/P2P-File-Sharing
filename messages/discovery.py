FILENAME_LENGTH_BYTES = 2
HOST_ID_LEN_BYTES = 4
SEQ_NUM_LEN_BYTES = 4
ENDIANNESS = 'little'


class Discovery:
    def __init__(self):
        self.__bytes = None
        self.__filename = None
        self.__src_host_id = None
        self.__dst_host_id = None
        self.__seq_num = None

    def get_filename(self):
        return self.__filename

    def get_src_host_id(self):
        return self.__src_host_id

    def get_dst_host_id(self):
        return self.__dst_host_id

    def get_seq_num(self):
        return self.__seq_num

    def get_bytes(self):
        return self.__bytes

    def set_packet_data(self, filename, src_host_id, dst_host_id, seq_num):
        self.__filename = filename
        self.__src_host_id = src_host_id
        self.__dst_host_id = dst_host_id
        self.__seq_num = seq_num

        self.__bytes = src_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        self.__bytes += dst_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        self.__bytes += seq_num.to_bytes(SEQ_NUM_LEN_BYTES, ENDIANNESS)

        filename_length = len(filename.encode('utf-8'))
        self.__bytes += filename_length.to_bytes(
            FILENAME_LENGTH_BYTES, ENDIANNESS)
        self.__bytes += filename.encode('utf-8')

    def set_bytes(self, _bytes):
        self.__bytes = _bytes
        if len(_bytes) < 2*HOST_ID_LEN_BYTES + SEQ_NUM_LEN_BYTES + FILENAME_LENGTH_BYTES:
            raise ValueError()

        cursor = 0
        self.__src_host_id = int.from_bytes(
            self.__bytes[cursor:cursor+HOST_ID_LEN_BYTES], ENDIANNESS)
        cursor += HOST_ID_LEN_BYTES
        self.__dst_host_id = int.from_bytes(
            self.__bytes[cursor:cursor+HOST_ID_LEN_BYTES], ENDIANNESS)
        cursor += HOST_ID_LEN_BYTES
        self.__seq_num = int.from_bytes(
            self.__bytes[cursor:cursor+SEQ_NUM_LEN_BYTES], ENDIANNESS)
        cursor += SEQ_NUM_LEN_BYTES

        filename_length = int.from_bytes(
            self.__bytes[cursor:cursor+FILENAME_LENGTH_BYTES], ENDIANNESS)
        cursor += FILENAME_LENGTH_BYTES

        if len(self.__bytes) != 2*HOST_ID_LEN_BYTES + FILENAME_LENGTH_BYTES + SEQ_NUM_LEN_BYTES + filename_length:
            raise ValueError()

        self.__filename = self.__bytes[cursor:].decode('utf-8')
