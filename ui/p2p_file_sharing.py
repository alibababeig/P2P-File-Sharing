import socket

FILENAME_LENGTH_BYTES = 2
ENDIANNESS = 'little'

BROADCAST_ADDR = '<broadcast>'
BROADCAST_PORT = 12345


class P2PFileSharing:
    def __init__(self):
        pass

    def request_file(self, filename):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        filename_length = len(filename).to_bytes(
            FILENAME_LENGTH_BYTES, ENDIANNESS)

        data = filename_length + filename.encode('utf-8')
        sock.sendto(data, (BROADCAST_ADDR, BROADCAST_PORT))
        sock.close()
