import bluetooth
from chunk_manager.file_chunker import FileChunker

EOT = b'\x04'

if __name__ == '__main__':
    file_path = './repository/tx_lake.jpg'
    chunk_size = 1000
    targetMac = '3c:f8:62:76:9a:89'
    port = 4

    file_chunker = FileChunker(file_path, chunk_size)
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((targetMac, port))

    chunk = file_chunker.get_next_chunk()
    while chunk != None:
        sock.send(chunk)
        chunk = file_chunker.get_next_chunk()

    sock.send(EOT)
    sock.close()
    file_chunker.close_file()
