import chunk


HOST_ID_LEN_BYTES = 4
SEQ_NUM_LEN_BYTES = 4
# FILE_CHUNK_LEN_BYTES = 2
FILENAME_LENGTH_BYTES = 2
FILESIZE_BYTES = 5
# CHUNK_SIZE_BYTES = 3
ENDIANNESS = 'little'


class Metadata:
    def __init__(self):
        self.__bytes = None
        self.__filesize = None
        self.__filename = None
        self.__src_host_id = None
        self.__dst_host_id = None
        self.__seq_num = None

    def get_filename(self):
        return self.__filename

    def get_filesize(self):
        return self.__filesize

    def get_src_host_id(self):
        return self.__src_host_id

    def get_dst_host_id(self):
        return self.__dst_host_id

    def get_seq_num(self):
        return self.__seq_num

    def get_bytes(self):
        return self.__bytes

    def set_packet_data(self, filename, filesize, src_host_id, dst_host_id, seq_num):
        self.__filename = filename
        self.__filesize = filesize
        self.__src_host_id = src_host_id
        self.__dst_host_id = dst_host_id
        self.__seq_num = seq_num

        _bytes = src_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += dst_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += seq_num.to_bytes(SEQ_NUM_LEN_BYTES, ENDIANNESS)

        encoded_filename = filename.encode('utf-8')
        _bytes += len(encoded_filename).to_bytes(FILENAME_LENGTH_BYTES, ENDIANNESS)
        _bytes += encoded_filename
        _bytes += filesize.to_bytes(FILESIZE_BYTES, ENDIANNESS)

        self.__bytes = _bytes

    def set_bytes(self, _bytes):
        self.__bytes = _bytes

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

        self.__filename = self.__bytes[cursor:cursor +
                                       filename_length].decode('utf-8')
        cursor += filename_length

        self.__filesize = int.from_bytes(
            self.__bytes[cursor:cursor+FILESIZE_BYTES], ENDIANNESS)
        cursor += FILESIZE_BYTES

        return cursor
