import bluetooth

if __name__ == '__main__':
    file_name = 'lake.jpg'
    myMac = 'a4:6b:b6:9b:2e:85'
    port = 4
    backlog = 1
    size = 100 * 1024

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.bind((myMac, port))
    sock.listen(backlog)

    try:
        client, clientInfo = sock.accept()
        data = client.recv(size)
        if data:
            f = open(f'./repository/rx_{file_name}', 'wb')
            f.write(data)
            f.close()
    except:	
        print("Closing socket")
        client.close()
        sock.close()
