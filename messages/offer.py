MATCH_CNT_BYTES = 1
HOST_ID_LEN_BYTES = 4
SEQ_NUM_LEN_BYTES = 4
FILENAME_LENGTH_BYTES = 2
FILESIZE_BYTES = 5
ENDIANNESS = 'little'


class Offer:
    def __init__(self):
        self.__bytes = None
        self.__matching_files = None
        self.__src_host_id = None
        self.__dst_host_id = None
        self.__seq_num = None


    def get_matching_files(self):
        return self.__matching_files

    def get_src_host_id(self):
        return self.__src_host_id

    def get_dst_host_id(self):
        return self.__dst_host_id

    def get_seq_num(self):
        return self.__seq_num
    
    def get_bytes(self):
        return self.__bytes

    def set_packet_data(self, matching_files, src_host_id, dst_host_id, seq_num):
        self.__matching_files = matching_files[:2**(MATCH_CNT_BYTES * 8)]
        self.__src_host_id = src_host_id
        self.__dst_host_id = dst_host_id
        self.__seq_num = seq_num

        # _bytes = bytes(map(int, src_host_id.split('.')))
        # _bytes += bytes(map(int, dst_host_id.split('.')))
        _bytes = src_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += dst_host_id.to_bytes(HOST_ID_LEN_BYTES, ENDIANNESS)
        _bytes += seq_num.to_bytes(SEQ_NUM_LEN_BYTES, ENDIANNESS)

        match_cnt = len(self.__matching_files)
        _bytes += match_cnt.to_bytes(MATCH_CNT_BYTES, ENDIANNESS)

        for dic in matching_files:
            filename = dic['name']
            filesize = dic['size']

            _bytes += len(filename.encode('utf-8')).to_bytes(
                FILENAME_LENGTH_BYTES, ENDIANNESS)
            _bytes += filename.encode('utf-8')
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

        match_cnt = int.from_bytes(
            self.__bytes[cursor:cursor+MATCH_CNT_BYTES], ENDIANNESS)
        cursor += MATCH_CNT_BYTES

        matching_files = []
        for i in range(match_cnt):
            filename_length = int.from_bytes(
                self.__bytes[cursor:cursor+FILENAME_LENGTH_BYTES], ENDIANNESS)
            cursor += FILENAME_LENGTH_BYTES

            filename = self.__bytes[cursor:cursor +
                                  filename_length].decode('utf-8')
            cursor += filename_length

            filesize = int.from_bytes(
                self.__bytes[cursor:cursor+FILESIZE_BYTES], ENDIANNESS)
            cursor += FILESIZE_BYTES

            matching_files.append({
                'name': filename,
                'size': filesize
            })

        if cursor != len(self.__bytes):
            raise ValueError()

        self.__matching_files = matching_files
