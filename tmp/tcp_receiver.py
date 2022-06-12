import socket

FILENAME_LENGTH_BYTES = 2
PAYLOAD_LENGTH_BYTES = 8
ENDIANNESS = 'little'

if __name__ == '__main__':
    repository = './repository/rx/'
    chunk_size = 1000
    my_port = 12345
    backlog = 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', my_port))
    sock.listen(backlog)

    client, clientInfo = sock.accept()
    buffer = b''
    while len(buffer) < PAYLOAD_LENGTH_BYTES + FILENAME_LENGTH_BYTES:
        buffer += client.recv(chunk_size)

    filename_length = int.from_bytes(
        buffer[:FILENAME_LENGTH_BYTES], ENDIANNESS)
    print(filename_length)

    payload_length = int.from_bytes(
        buffer[FILENAME_LENGTH_BYTES:
               FILENAME_LENGTH_BYTES + PAYLOAD_LENGTH_BYTES], ENDIANNESS)
    print(payload_length)

    buffer = buffer[FILENAME_LENGTH_BYTES + PAYLOAD_LENGTH_BYTES:]
    while len(buffer) < filename_length:
        buffer += client.recv(chunk_size)

    filename = buffer[:filename_length].decode('utf-8')
    print(filename)

    f = open(repository + filename, 'wb')
    written_bytes = 0

    buffer = buffer[filename_length:]
    while written_bytes < payload_length:
        f.write(buffer)
        written_bytes += len(buffer)
        buffer = client.recv(chunk_size)

    client.close()
    sock.close()
    f.close()
