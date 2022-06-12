import socket
from chunk_manager.file_chunker import FileChunker

FILENAME_LENGTH_BYTES = 2
PAYLOAD_LENGTH_BYTES = 8
ENDIANNESS = 'little'

if __name__ == '__main__':
    filename = 'lake.jpg'
    file_path = f'./repository/tx/{filename}'
    chunk_size = 1000
    target_ip = '127.0.0.1'
    target_port = 12345

    file_chunker = FileChunker(file_path, chunk_size)

    filename_length = len(filename.encode(
        'utf-8')).to_bytes(FILENAME_LENGTH_BYTES, ENDIANNESS)

    payload_length = file_chunker.get_file_size().to_bytes(
        PAYLOAD_LENGTH_BYTES, ENDIANNESS)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((target_ip, target_port))

    sock.send(filename_length)
    sock.send(payload_length)
    sock.send(filename.encode("utf-8"))

    chunk = file_chunker.get_next_chunk()
    while chunk != None:
        sock.send(chunk)
        chunk = file_chunker.get_next_chunk()

    sock.close()
    file_chunker.close_file()
