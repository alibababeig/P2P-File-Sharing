import os
import random
import threading  # FIXME:
import time

from collections import defaultdict

from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, \
    SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST
from chunk_manager.file_chunker import FileChunker

from messages.ack import Ack
from messages.discovery import Discovery
from messages.offer import Offer

from ui.Cli import Cli


FILENAME_LENGTH_BYTES = 2
ENDIANNESS = 'little'

BROADCAST_ADDR = '<broadcast>'
BROADCAST_PORT = 12345

RX_REPO_PATH = './repository/rx'
TX_REPO_PATH = './repository/tx'

TRANSMISSION_TIMEOUT = 1  # seconds
OFFER_TIMEOUT = 5  # seconds
ACK_TIMEOUT = 30  # seconds

CHUNK_SIZE = 10000  # Bytes


class P2PFileSharing:
    def __init__(self):
        self.discovery_sock = None
        self.offerer_sock = socket(AF_INET, SOCK_DGRAM)
        self.data_receiver_sock = None
        self.data_sender_sock = None  # TODO

        self.listener_sock = socket(AF_INET, SOCK_DGRAM)
        self.listener_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.listener_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.listener_sock.bind('', BROADCAST_PORT)

        threading.Thread(target=self.__listen).start()
        threading.Thread(target=self.__get_ack).start()

    def request_file(self, req_filename):
        self.__send_discovery(req_filename)

        offers = self.__get_offers()
        Cli.show_offers(offers)

        choice = Cli.choose_offer(offers)
        self.__send_ack(choice)

        filename = choice[1]['name']
        filesize = choice[1]['size']
        self.__receive_data(filename, filesize)

    def __send_discovery(self, req_filename):
        self.discovery_sock = socket(AF_INET, SOCK_DGRAM)
        self.discovery_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.discovery_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        discovery = Discovery()
        discovery.set_filename(req_filename)

        self.discovery_sock.sendto(
            discovery.get_bytes(), (BROADCAST_ADDR, BROADCAST_PORT))

    def __listen(self):
        buffer = defaultdict(bytes)
        timestamps = defaultdict(int)
        current_client = None

        while True:
            if current_client is None:
                rec_bytes, client = self.listener_sock.recvfrom(
                    FILENAME_LENGTH_BYTES)  # FIXME: Should be non-blocking
                if timestamps[client] == 0:
                    timestamps[client] = time.time()
                buffer[client] += rec_bytes
                current_client = client

            else:
                discovery = Discovery()
                try:
                    # The following line may raise an exception
                    discovery.set_bytes(buffer[current_client])
                    self.__send_offer(discovery.get_filename, current_client)
                except ValueError:
                    if not self.__is_expired(timestamps[current_client],
                                             TRANSMISSION_TIMEOUT):
                        rec_bytes, client = self.listener_sock.recvfrom(
                            FILENAME_LENGTH_BYTES)  # FIXME: Should be non-blocking
                        if timestamps[client] == 0:
                            timestamps[client] = time.time()
                        buffer[client] += rec_bytes
                        continue
                finally:
                    del buffer[current_client]
                    del timestamps[current_client]

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
        ack = self.__get_ack(client)

    def __get_offers(self):
        start_time = time.time()

        offers = {}
        buffer = defaultdict(bytes)
        timestamps = defaultdict(int)
        current_offerer = None

        while not self.__is_expired(start_time, OFFER_TIMEOUT):
            if current_offerer is None:
                rec_bytes, offerer = self.discovery_sock.recvfrom(
                    FILENAME_LENGTH_BYTES)  # FIXME: Should be non-blocking
                if timestamps[offerer] == 0:
                    timestamps[offerer] = time.time()
                buffer[offerer] += rec_bytes
                current_offerer = offerer

            else:
                offer = Offer()
                try:
                    # The following line may raise an exception
                    offer.set_bytes(buffer[current_offerer])
                    offers[current_offerer] = offer.get_matching_files()
                except ValueError:
                    if not self.__is_expired(timestamps[current_offerer],
                                             TRANSMISSION_TIMEOUT):
                        rec_bytes, offerer = self.discovery_sock.recvfrom(
                            FILENAME_LENGTH_BYTES)  # FIXME: Should be non-blocking
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

    def __send_ack(self, choice):
        offerer, dic = choice
        filename = dic['name']

        port_number = random.randint(1024, 65535)
        self.data_receiver_sock = socket(AF_INET, SOCK_STREAM)
        self.data_receiver_sock.bind(('', port_number))  # TODO: Handle failure

        ack = Ack()
        ack.set_data(filename, port_number)
        self.discovery_sock.sendto(ack.get_bytes(), offerer)

        self.discovery_sock.close()

    def __get_ack(self, client):
        buffer = defaultdict(bytes)
        timestamps = defaultdict(int)
        current_client = None

        while True:
            if current_client is None:
                rec_bytes, client = self.offerer_sock.recvfrom(CHUNK_SIZE)
                if timestamps[client] == 0:
                    timestamps[client] = time.time()
                buffer[client] += rec_bytes
                current_client = client

            else:
                ack = Ack()
                try:
                    # The following line may raise an exception
                    ack.set_bytes(buffer[current_client])
                    filename = ack.get_filename()
                    final_addr = (current_client[0], ack.get_port_number())
                    threading.Thread(target=self.__send_data,
                                     args=(filename, final_addr)).start()
                except ValueError:
                    if not self.__is_expired(timestamps[current_client],
                                             TRANSMISSION_TIMEOUT):
                        rec_bytes, client = self.offerer_sock.recvfrom(
                            CHUNK_SIZE)
                        if timestamps[client] == 0:
                            timestamps[client] = time.time()
                        buffer[client] += rec_bytes
                        continue
                finally:
                    del buffer[current_client]
                    del timestamps[current_client]

                    if len(list(buffer.keys())) > 0:
                        current_client = list(buffer.keys())[0]
                    else:
                        current_client = None

    def __send_data(self, filename, client):
        self.data_sender_sock = socket(AF_INET, SOCK_STREAM)
        self.connect(client)

        file_chunker = FileChunker(
            os.path.join(TX_REPO_PATH, filename), CHUNK_SIZE)

        chunk = file_chunker.get_next_chunk()
        while chunk != None:
            self.data_sender_sock.send(chunk)
            chunk = file_chunker.get_next_chunk()

        file_chunker.close_file()
        self.data_sender_sock.close()

    def __receive_data(self, filename, filesize):
        self.data_receiver_sock.listen(1)
        sock, _ = self.data_receiver_sock.accept()

        f = open(os.path.join(RX_REPO_PATH, filename), 'wb')
        written_bytes = 0

        while written_bytes < filesize:
            buffer = sock.recv(CHUNK_SIZE)  # FIXME: Should be non-blocking
            f.write(buffer)
            written_bytes += len(buffer)

        f.close()
        self.data_receiver_sock.close()

    def __is_expired(self, timestamp, timout):
        if timestamp == 0:
            return False
        return time.time() - timestamp < timout
