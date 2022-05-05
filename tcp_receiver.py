import socket

EOT = b'\x04'

if __name__ == '__main__':
    file_path = './repository/rx_lake.jpg'
    chunk_size = 1000
    port = 12345
    backlog = 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(backlog)

    try:
        client, clientInfo = sock.accept()
        f = open(file_path, 'wb')
        while True:
            data = client.recv(chunk_size)
            if data:
                if data[-1:] == EOT:
                    f.write(data[:-1])
                    break
                else:
                    f.write(data)

        client.close()
        sock.close()
        f.close()
    except:
        print("Closing socket")
        client.close()
        sock.close()
