import os
import socket
import threading
from collections import defaultdict

from packets.discovery import Discovery
from packets.offer import Offer

FILENAME_LENGTH_BYTES = 2
ENDIANNESS = 'little'

BROADCAST_ADDR = '<broadcast>'
BROADCAST_PORT = 12345

RX_REPO_PATH = './repository/rx'
TX_REPO_PATH = './repository/tx'


class P2PFileSharing:
    def __init__(self):
        self.listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listener_sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listener_sock.bind('', BROADCAST_PORT)

        self.offerer_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.data_sender_sock = None  # TODO

        self.data_receiver_sock = None  # TODO

        threading.Thread(target=self.__listen).start()

    def request_file(self, filename):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        discovery = Discovery()
        discovery.set_filename(filename)

        sock.sendto(discovery.get_bytes(), (BROADCAST_ADDR, BROADCAST_PORT))

        # TODO: Get offers

        sock.close()

    def __listen(self):
        buffer = defaultdict(bytes)
        current_client = None
        while True:
            if current_client is None:
                rec_bytes, client = self.listener_sock.recvfrom(
                    FILENAME_LENGTH_BYTES)
                buffer[client] += rec_bytes
                current_client = client

            else:
                discovery = Discovery()
                try:
                    discovery.set_bytes(buffer[current_client])
                except Exception:
                    rec_bytes, client = self.listener_sock.recvfrom(
                        FILENAME_LENGTH_BYTES)
                    buffer[client] += rec_bytes
                    continue

                self.__send_offer(discovery.get_filename, current_client)
                del buffer[current_client]
                if len(list(buffer.keys())) > 0:
                    current_client = list(buffer.keys())[0]
                else:
                    current_client = None

    def __send_offer(self, req_filename, client):
        tx_filenames = [
            filename
            for filename in os.listdir(TX_REPO_PATH)
            if os.path.isfile(os.path.join(TX_REPO_PATH, filename))
        ]

        matching_files = [
            {
                'name': filename,
                'size': os.path.getsize(os.path.join(TX_REPO_PATH, filename))
            }
            for filename in tx_filenames
            if req_filename in filename
        ]

        if len(matching_files) == 0:
            return

        offer = Offer(matching_files=matching_files)
        self.offerer_sock.sendto(offer.get_bytes(), client)
