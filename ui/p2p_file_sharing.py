import os
import socket
import threading
from collections import defaultdict
import time

from messages.discovery import Discovery
from messages.offer import Offer

FILENAME_LENGTH_BYTES = 2
ENDIANNESS = 'little'

BROADCAST_ADDR = '<broadcast>'
BROADCAST_PORT = 12345

RX_REPO_PATH = './repository/rx'
TX_REPO_PATH = './repository/tx'

TRANSMISSION_TIMEOUT = 1  # seconds
OFFER_TIMEOUT = 5  # seconds


class P2PFileSharing:
    def __init__(self):
        self.discovery_sock = None

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
        self.discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.discovery_sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        discovery = Discovery()
        discovery.set_filename(filename)

        self.discovery_sock.sendto(
            discovery.get_bytes(), (BROADCAST_ADDR, BROADCAST_PORT))

        offers = self.__get_offers()
        self.show_offers(offers)

        self.discovery_sock.close()

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
                    # TODO: add some timeout mechanism
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

    def __get_offers(self):
        start_time = time.time()

        offers = {}
        buffer = defaultdict(bytes)
        timestamps = defaultdict(int)
        current_offerer = None

        while time.time() - start_time < OFFER_TIMEOUT:
            if current_offerer is None:
                rec_bytes, offerer = self.discovery_sock.recvfrom(
                    FILENAME_LENGTH_BYTES)
                if timestamps[offerer] == 0:
                    timestamps[offerer] = time.time()
                buffer[offerer] += rec_bytes
                current_offerer = offerer

            else:
                offer = Offer()
                try:
                    # The following line may raises an exception
                    offer.set_bytes(buffer[current_offerer])
                    offers[current_offerer] = offer.get_matching_files()
                except Exception:
                    if not self.__is_expired(timestamps[current_offerer]):
                        rec_bytes, offerer = self.discovery_sock.recvfrom(
                            FILENAME_LENGTH_BYTES)
                        if timestamps[offerer] == 0:
                            timestamps[offerer] = time.time()
                        buffer[offerer] += rec_bytes
                        continue
                finally:
                    del buffer[current_offerer]
                    del timestamps[current_offerer]

                    if len(list(buffer.keys())) > 0:
                        current_offerer = list(buffer.keys())[0]
                    else:
                        current_offerer = None

        return offers

    def __is_expired(self, timestamp):
        if timestamp == 0:
            return False

        return time.time() - timestamp < TRANSMISSION_TIMEOUT
