FILENAME_LENGTH_BYTES = 2
PORT_NUMBER_BYTES = 2
HOST_ID_LEN_BYTES = 4
SEQ_NUM_LEN_BYTES = 4
ENDIANNESS = 'little'


class Ack:
    def __init__(self):
        self.__bytes = None
        self.__data = None
        self.__src_host_id = None
        self.__dst_host_id = None
        self.__seq_num = None

    def get_filename(self):
        return self.__data

    def get_bytes(self):
        return self.__bytes

    def get_src_host_id(self):
        return self.__src_host_id

    def get_dst_host_id(self):
        return self.__dst_host_id

    def get_seq_num(self):
        return self.__seq_num

    def set_packet_data(self, filename, src_host_id, dst_host_id, seq_num):
        self.__data = filename
        self.__src_host_id = src_host_id
        self.__dst_host_id = dst_host_id
        self.__seq_num = seq_num

        _bytes = src_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += dst_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += seq_num.to_bytes(SEQ_NUM_LEN_BYTES, ENDIANNESS)

        filename_length = len(filename.encode('utf-8'))
        _bytes += filename_length.to_bytes(FILENAME_LENGTH_BYTES, ENDIANNESS)
        _bytes += filename.encode('utf-8')
        # _bytes += port_number.to_bytes(PORT_NUMBER_BYTES, ENDIANNESS)

        self.__bytes = _bytes

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
            _bytes[cursor:cursor+FILENAME_LENGTH_BYTES], ENDIANNESS)
        cursor += FILENAME_LENGTH_BYTES

        self.__data = _bytes[cursor:
                          cursor + filename_length].decode('utf-8')
        # cursor += filename_length
        # port_number = int.from_bytes(
        #     _bytes[cursor:], ENDIANNESS)

        if len(_bytes) != 2*HOST_ID_LEN_BYTES + SEQ_NUM_LEN_BYTES + \
                FILENAME_LENGTH_BYTES + filename_length:
            raise ValueError()
