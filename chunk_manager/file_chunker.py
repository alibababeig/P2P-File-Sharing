import os


class FileChunker:
    def __init__(self, file_path, chunk_size=10000):
        self.file = open(file_path, 'rb')
        self.chunk_size = chunk_size

    def get_file_size(self):
        return os.path.getsize(self.file.name)

    def get_next_chunk(self):
        chunk = self.file.read(self.chunk_size)
        return chunk if chunk != b'' else None

    def close_file(self):
        self.file.close()
