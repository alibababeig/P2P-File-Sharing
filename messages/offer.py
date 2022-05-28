MATCH_CNT_BYTES = 1
FILENAME_LENGTH_BYTES = 2
FILESIZE_BYTES = 5
ENDIANNESS = 'little'


class Offer:
    def __init__(self):
        self.matching_files = None
        self.bytes = None

    def get_matching_files(self):
        return self.matching_files

    def set_matching_files(self, matching_files):
        self.matching_files = matching_files[:2**(MATCH_CNT_BYTES * 8)]

        match_cnt = len(self.matching_files)
        _bytes = match_cnt.to_bytes(MATCH_CNT_BYTES, ENDIANNESS)

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

        match_cnt = int.from_bytes(
            self.bytes[:MATCH_CNT_BYTES], ENDIANNESS)
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

        self.matching_files = matching_files
