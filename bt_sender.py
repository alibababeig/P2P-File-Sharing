import bluetooth

if __name__ == '__main__':
    targetMac = '00:1f:e1:dd:08:3d'
    port = 4
    
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((targetMac, port))

    while 1:
        text = input()
        if text == "quit":
            break
        sock.send(text)
    sock.close()
