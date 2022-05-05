import bluetooth

if __name__ == '__main__':
    myMac = ''
    port = 4
    backlog = 1
    size = 1024

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.bind((myMac, port))
    sock.listen(backlog)

    try:
        client, clientInfo = sock.accept()
        while 1:
            data = client.recv(size)
            if data:
                print(data)
                client.send(data) # Echo back to client
    except:	
        print("Closing socket")
        client.close()
        sock.close()
