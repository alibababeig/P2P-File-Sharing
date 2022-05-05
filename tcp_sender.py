import socket
from chunk_manager.file_chunker import FileChunker

EOT = b'\x04'

if __name__ == '__main__':
    file_path = './repository/tx_lake.jpg'
    chunk_size = 1000
    targetIp = '192.168.1.111'
    port = 12345

    file_chunker = FileChunker(file_path, chunk_size)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((targetIp, port))

    chunk = file_chunker.get_next_chunk()
    while chunk != None:
        sock.send(chunk)
        chunk = file_chunker.get_next_chunk()

    sock.send(EOT)
    sock.close()
    file_chunker.close_file()
