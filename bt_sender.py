import bluetooth

if __name__ == '__main__':
    file_name = 'lake.jpg'
    targetMac = '3c:f8:62:76:9a:89'
    port = 4
    
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((targetMac, port))

    f = open(f'./repository/tx_{file_name}', 'rb')
    sock.send(f.read())
    f.close()

    sock.close()
