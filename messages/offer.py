MATCH_CNT_BYTES = 1
IP_LEN_BYTES = 4
FILENAME_LENGTH_BYTES = 2
FILESIZE_BYTES = 5
ENDIANNESS = 'little'


class Offer:
    def __init__(self):
        self.bytes = None
        self.matching_files = None
        self.src_addr = None
        self.dst_addr = None

    def get_matching_files(self):
        return self.matching_files

    def get_src_addr(self):
        return self.src_addr

    def get_dst_addr(self):
        return self.dst_addr

    def set_matching_files(self, matching_files, src_addr, dst_addr):
        self.matching_files = matching_files[:2**(MATCH_CNT_BYTES * 8)]
        self.src_addr = src_addr
        self.dst_addr = dst_addr

        _bytes = bytes(map(int, src_addr.split('.')))
        _bytes += bytes(map(int, dst_addr.split('.')))

        match_cnt = len(self.matching_files)
        _bytes += match_cnt.to_bytes(MATCH_CNT_BYTES, ENDIANNESS)

        for dic in matching_files:
            filename = dic['name']
            filesize = dic['size']

            _bytes += len(filename.encode('utf-8')).to_bytes(
                FILENAME_LENGTH_BYTES, ENDIANNESS)
            _bytes += filename.encode('utf-8')
            _bytes += filesize.to_bytes(FILESIZE_BYTES, ENDIANNESS)

        self.bytes = _bytes

    def get_bytes(self):
        return self.bytes

    def set_bytes(self, _bytes):
        self.bytes = _bytes
        cursor = 0

        self.src_addr = ''
        for i in range(IP_LEN_BYTES):
            self.src_addr += str(int.from_bytes(self.bytes[cursor:cursor+1], ENDIANNESS)) + ('' if i == IP_LEN_BYTES-1 else '.')
            cursor += 1
        self.dst_addr = ''
        for i in range(IP_LEN_BYTES):
            self.dst_addr += str(int.from_bytes(self.bytes[cursor:cursor+1], ENDIANNESS)) + ('' if i == IP_LEN_BYTES-1 else '.')
            cursor += 1

        match_cnt = int.from_bytes(
            self.bytes[cursor:cursor+MATCH_CNT_BYTES], ENDIANNESS)
        cursor += MATCH_CNT_BYTES

        matching_files = []
        for i in range(match_cnt):
            filename_length = int.from_bytes(
                self.bytes[cursor:cursor+FILENAME_LENGTH_BYTES], ENDIANNESS)
            cursor += FILENAME_LENGTH_BYTES

            filename = self.bytes[cursor:cursor +
                                  filename_length].decode('utf-8')
            cursor += filename_length

            filesize = int.from_bytes(
                self.bytes[cursor:cursor+FILESIZE_BYTES], ENDIANNESS)
            cursor += FILESIZE_BYTES

            matching_files.append({
                'name': filename,
                'size': filesize
            })

        if cursor != len(self.bytes):
            raise ValueError()

        self.matching_files = matching_files
