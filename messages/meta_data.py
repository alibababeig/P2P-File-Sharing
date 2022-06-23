import chunk


HOST_ID_LEN_BYTES = 4
SEQ_NUM_LEN_BYTES = 4
FILE_CHUNK_LEN_BYTES = 2
CHUNK_SIZE_BYTES = 3
ENDIANNESS = 'little'


class Data:
    def __init__(self):
        self.__bytes = None
        self.__chunk = None
        self.__filesize = None
        self.__src_host_id = None
        self.__dst_host_id = None
        self.__seq_num = None


    def get_file_chunk(self):
        return self.__chunk

    # def get_filesize(self):
    #     return self.__filesize

    def get_src_host_id(self):
        return self.__src_host_id

    def get_dst_host_id(self):
        return self.__dst_host_id

    def get_seq_num(self):
        return self.__seq_num
    
    def get_bytes(self):
        return self.__bytes

    def set_packet_data(self, chunk, filesize, src_host_id, dst_host_id, seq_num):
        self.__chunk = chunk
        # self.__filesize = filesize
        self.__src_host_id = src_host_id
        self.__dst_host_id = dst_host_id
        self.__seq_num = seq_num

        _bytes = src_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += dst_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += seq_num.to_bytes(SEQ_NUM_LEN_BYTES, ENDIANNESS)

        chunk_size = len(self.__chunk)
        _bytes += chunk_size.to_bytes(CHUNK_SIZE_BYTES, ENDIANNESS)

        _bytes += chunk
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

        chunk_size = int.from_bytes(
            self.__bytes[cursor:cursor+CHUNK_SIZE_BYTES], ENDIANNESS)
        cursor += CHUNK_SIZE_BYTES

        chunk = self.__bytes[cursor:cursor+chunk_size], ENDIANNESS)
        cursor += chunk_size



        if cursor != len(self.__bytes):
            raise ValueError()

        self.__matching_files = matching_files
