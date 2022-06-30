import os
import configparser
import random
import threading
import time

from difflib import SequenceMatcher
from socket import socket, AF_INET, SOCK_STREAM, timeout
from threading import Thread

from chunk_manager.file_chunker import FileChunker
from messages.ack import Ack
from messages.discovery import Discovery
from messages.metadata import Metadata
from messages.offer import Offer
from messages.packet_type import PacketType
from ui.cli import Cli
from status.status import Status

FILENAME_LENGTH_BYTES = 2
PACKET_TYPE_BYTES = 1
ENDIANNESS = 'little'

RX_PORT = 3773

RX_REPO_PATH = './repository/rx'
TX_REPO_PATH = './repository/tx'

TRANSMISSION_TIMEOUT = 1  # seconds
OFFER_TIMEOUT = 4  # seconds
DATA_TRANSFER_TIMEOUT = 5  # seconds
RECENT_PACKET_EXPIRATION = 10  # seconds

MIN_PORT = 1024
MAX_PORT = 65535

SIMILARITY_THRESHOLD = 0.5
TOPOLOGY_CONFIG_PATH = './topology.conf'
BACKLOG_COUNT = 5
BROADCAST_ID = 2 ** 32 - 1
EPSILON = 0.0001


class P2PFileSharing:
    def __init__(self, chunck_size=10000):
        self.chunk_size = chunck_size  # Bytes

        self.__rx_sock = socket(AF_INET, SOCK_STREAM)
        self.__rx_sock.bind(('', RX_PORT))

        self.__routing_dict = dict()
        self.__routing_dict_lock = threading.Lock()
        self.__offers_dict = dict()
        self.__offers_dict_flag = False

        # read from conf file
        config = configparser.ConfigParser()
        config.read(TOPOLOGY_CONFIG_PATH)
        self.__host_id = int(config['Self']['HOST_ID'].replace(' ', ''))
        self.__neighbour_ips = config['Neighbours']['HOST_IPS'].replace(
            ' ', '').split(',')

        self.__seq_num = random.randint(0, 2**32-1)
        self.__seq_num_lock = threading.Lock()

        self.__recent_packets = []
        self.__recent_packets_lock = threading.Lock()

        Thread(target=self.__receive).start()

    def request_file(self):
        Cli.print_log('enter your query:', 'Info')
        req_filename = input()
        Cli.print_log('LOG: request_file(' + req_filename + ')', 'Debug')

        self.__offers_dict_flag = True
        self.__send_discovery(req_filename)
        # clear prev offers
        self.__offers_dict = dict()
        time.sleep(OFFER_TIMEOUT)
        self.__offers_dict_flag = False
        offers = self.__offers_dict
        Cli.show_offers(offers)
        if len(offers) == 0:
            return Status.NO_OFFERS

        choice = Cli.choose_offer(offers)
        if choice == None:
            return Status.NO_CHOICE

        self.__send_ack(choice)

    def __send_discovery(self, req_filename):
        Cli.print_log('LOG: __send_discovery(' + req_filename + ')', 'Debug')

        with self.__seq_num_lock:
            curr_seq_num = self.__seq_num
            self.__seq_num += 1
        discovery = Discovery()
        discovery.set_packet_data(
            req_filename, self.__host_id, BROADCAST_ID, curr_seq_num)
        for neighbour in self.__neighbour_ips:
            Thread(target=self.__send_discovery_to_neighbour,
                   args=(discovery, neighbour)).start()

    def __send_discovery_to_neighbour(self, discovery_packet, neighbour_ip):
        discovery_sock = socket(AF_INET, SOCK_STREAM)
        discovery_sock.settimeout(DATA_TRANSFER_TIMEOUT)
        try:
            discovery_sock.connect((neighbour_ip, RX_PORT))
        except:
            Cli.print_log(
                f'connection to {neighbour_ip}:{RX_PORT} refused', 'Error')
            return

        packet_type_bytes = PacketType.DISCOVERY.value.to_bytes(
            PACKET_TYPE_BYTES, ENDIANNESS)
        try:
            discovery_sock.send(packet_type_bytes +
                                discovery_packet.get_bytes())
        except:
            Cli.print_log('\ntransmission interrupted', 'Error')

        discovery_sock.close()

    def __receive(self):
        Cli.print_log('LOG: __listen()', 'Debug')

        self.__rx_sock.listen(BACKLOG_COUNT)
        while True:
            sock, sender_addr = self.__rx_sock.accept()
            sock.settimeout(DATA_TRANSFER_TIMEOUT)
            Thread(target=self.__handle_connection,
                   args=(sock, sender_addr)).start()

    def __handle_connection(self, rec_sock, sender_addr):
        buff = b''
        while len(buff) < 9:
            try:
                buff += rec_sock.recv(self.chunk_size)
            except:
                Cli.print_log('\ntransmission interrupted', 'Error')
                return

        packet_type = int.from_bytes(buff[:1], ENDIANNESS)
        src_host_id = int.from_bytes(buff[1:5], ENDIANNESS)
        dst_host_id = int.from_bytes(buff[5:9], ENDIANNESS)
        with self.__routing_dict_lock:
            self.__routing_dict[src_host_id] = sender_addr[0]

        if packet_type == PacketType.DISCOVERY.value:
            p = Discovery()
        elif packet_type == PacketType.OFFER.value:
            p = Offer()
        elif packet_type == PacketType.ACK.value:
            p = Ack()
        elif packet_type == PacketType.METADATA.value:
            p = Metadata()
        else:
            rec_sock.close()
            return

        if dst_host_id != self.__host_id and packet_type != PacketType.DISCOVERY.value:
            self.__redirect_packet(p, buff, dst_host_id, packet_type, rec_sock)
            rec_sock.close()
        else:
            while True:
                try:
                    cursor = p.set_bytes(buff[PACKET_TYPE_BYTES:])
                    break
                except:
                    try:
                        buff += rec_sock.recv(self.chunk_size)
                    except:
                        Cli.print_log('\ntransmission interrupted', 'Error')
                        return

            if packet_type == PacketType.METADATA.value:
                buff = buff[PACKET_TYPE_BYTES + cursor:]
                self.__process_data_packet(p, buff, rec_sock)
                rec_sock.close()
            else:
                rec_sock.close()
                self.__process_packet(
                    p, packet_type, src_host_id, sender_addr[0])

    def __redirect_packet(self, packet, buff, dst_host_id, packet_type, rec_sock):
        if dst_host_id not in self.__routing_dict:
            return

        send_sock = socket(AF_INET, SOCK_STREAM)
        try:
            send_sock.connect((self.__routing_dict[dst_host_id], RX_PORT))
        except:
            Cli.print_log(
                f'connection to {self.__routing_dict[dst_host_id]}:{RX_PORT} refused', 'Error')
            return
        send_sock.setblocking(0)
        send_sock.settimeout(DATA_TRANSFER_TIMEOUT)
        cursor = 0

        if packet_type == PacketType.METADATA.value:
            while True:
                try:
                    send_sock.send(buff[cursor:])
                except:
                    Cli.print_log('\ntransmission interrupted', 'Error')
                    return
                cursor = len(buff)
                try:
                    cursor = packet.set_bytes(buff[PACKET_TYPE_BYTES:])
                    break
                except:
                    try:
                        buff += rec_sock.recv(self.chunk_size)
                    except:
                        Cli.print_log('\ntransmission interrupted', 'Error')
                        send_sock.close()
                        return
            filesize = packet.get_filesize()
            written_bytes = len(buff[PACKET_TYPE_BYTES + cursor:])
            start_time = time.time()
            while written_bytes < filesize:
                try:
                    buff = rec_sock.recv(self.chunk_size)
                    send_sock.send(buff)
                except:
                    Cli.print_log('\ntransmission interrupted', 'Error')
                    break
                written_bytes += len(buff)
                download_speed = self.__calc_speed(written_bytes, start_time)
                Cli.print_progress_bar(written_bytes, filesize, download_speed)
            return

        while True:
            try:
                send_sock.send(buff[cursor:])
            except:
                Cli.print_log('\ntransmission interrupted', 'Error')
                break
            cursor += len(buff)
            try:
                packet.set_bytes(buff[PACKET_TYPE_BYTES:])
                return
            except:
                try:
                    buff += rec_sock.recv(self.chunk_size)
                except:
                    Cli.print_log('\ntransmission interrupted', 'Error')
                    break

    def __process_packet(self, packet, packet_type, src_host_id, sender_ip):
        if packet_type == PacketType.DISCOVERY.value:
            pkt_src_id = packet.get_src_host_id()
            pkt_seq_num = packet.get_seq_num()
            timestamp = time.time()

            if pkt_src_id == self.__host_id:
                return

            with self.__recent_packets_lock:
                for i, arr in enumerate(self.__recent_packets):
                    if pkt_src_id == arr[0] and pkt_seq_num == arr[1]:
                        if timestamp > arr[2]:
                            self.__recent_packets[i][2] = timestamp
                        return
                self.__update_recent_packets(
                    pkt_src_id, pkt_seq_num, timestamp)

            self.__send_offer(packet.get_filename(), src_host_id)
            for neighbour in self.__neighbour_ips:
                if neighbour != sender_ip:
                    Thread(target=self.__send_discovery_to_neighbour(
                        packet, neighbour)).start()
        elif packet_type == PacketType.OFFER.value:
            if self.__offers_dict_flag:
                self.__offers_dict[packet.get_src_host_id()] = packet.get_matching_files(
                )
        elif packet_type == PacketType.ACK.value:
            self.__send_data(packet.get_filename(), src_host_id)
        else:
            Cli.print_log('Unknown packet type', 'Error')

    def __process_data_packet(self, metadata_packet, buff, rec_sock):
        filename = metadata_packet.get_filename()
        filesize = metadata_packet.get_filesize()
        Cli.print_log('LOG: __process_data_packet(' + filename +
                      ', ' + str(filesize) + ')', 'Debug')
        buffer = buff

        f = open(os.path.join(RX_REPO_PATH, filename), 'wb')
        written_bytes = 0
        status = Status.SUCCESS
        start_time = time.time()
        timer_start_time = start_time

        while written_bytes < filesize:
            f.write(buffer)
            written_bytes += len(buffer)

            try:
                buffer = rec_sock.recv(self.chunk_size)
                if len(buffer) > 0:
                    timer_start_time = time.time()
                if self.__is_expired(timer_start_time, DATA_TRANSFER_TIMEOUT):
                    raise timeout
            except:
                status = Status.TRANSFER_INTERRUPTED
                Cli.print_log('\ntransmission interrupted', 'Error')
                break

            download_speed = self.__calc_speed(written_bytes, start_time)
            Cli.print_progress_bar(written_bytes, filesize, download_speed)

        f.close()

        return status

    def __send_offer(self, req_filename, dst_host_id):
        client = (self.__routing_dict[dst_host_id], RX_PORT)
        Cli.print_log('LOG: __send_offer(' + req_filename +
                      ', ' + str(client) + ')', 'Debug')
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
            if req_filename.lower() in filename.lower() or
            SequenceMatcher(None, req_filename.lower(),
                            filename.lower()).ratio() > SIMILARITY_THRESHOLD
        ]

        if len(matching_files) == 0:
            return

        with self.__seq_num_lock:
            curr_seq_num = self.__seq_num
            self.__seq_num += 1
        offer = Offer()
        offer.set_packet_data(
            matching_files, self.__host_id, dst_host_id, curr_seq_num)

        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(DATA_TRANSFER_TIMEOUT)
        try:
            sock.connect(client)
        except:
            Cli.print_log(
                f'connection to {client[0]}:{client[1]} refused', 'Error')
            return

        packet_type_bytes = PacketType.OFFER.value.to_bytes(
            PACKET_TYPE_BYTES, ENDIANNESS)
        try:
            sock.send(packet_type_bytes + offer.get_bytes())
        except:
            Cli.print_log('\ntransmission interrupted', 'Error')

        sock.close()

    def __send_ack(self, choice):
        Cli.print_log('LOG: __send_ack(' + str(choice) + ')', 'Debug')
        offerer_id, dic = choice
        filename = dic['name']
        filesize = dic['size']

        ack = Ack()
        with self.__seq_num_lock:
            curr_seq_num = self.__seq_num
            self.__seq_num += 1
        ack.set_packet_data(filename, self.__host_id, offerer_id, curr_seq_num)

        ack_sender_sock = socket(AF_INET, SOCK_STREAM)
        try:
            ack_sender_sock.connect((self.__routing_dict[offerer_id], RX_PORT))
        except:
            Cli.print_log(
                f'connection to {self.__routing_dict[offerer_id]}:{RX_PORT} refused', 'Error')
            return
        ack_sender_sock.setblocking(0)
        ack_sender_sock.settimeout(DATA_TRANSFER_TIMEOUT)

        packet_type_bytes = PacketType.ACK.value.to_bytes(
            PACKET_TYPE_BYTES, ENDIANNESS)
        try:
            ack_sender_sock.send(packet_type_bytes + ack.get_bytes())
        except:
            Cli.print_log('\ntransmission interrupted', 'Error')

        ack_sender_sock.close()

    def __send_data(self, filename, client_id):
        Cli.print_log('LOG: __send_data(' + filename +
                      ', ' + str(client_id) + ')', 'Debug')

        data_sender_sock = socket(AF_INET, SOCK_STREAM)
        try:
            data_sender_sock.connect((self.__routing_dict[client_id], RX_PORT))
        except:
            Cli.print_log(
                f'connection to {self.__routing_dict[client_id]}:{RX_PORT} refused', 'Error')
            return
        data_sender_sock.setblocking(0)
        data_sender_sock.settimeout(DATA_TRANSFER_TIMEOUT)

        file_chunker = FileChunker(
            os.path.join(TX_REPO_PATH, filename), self.chunk_size)

        with self.__seq_num_lock:
            curr_seq_num = self.__seq_num
            self.__seq_num += 1

        filesize = file_chunker.get_file_size()

        metadata = Metadata()
        metadata.set_packet_data(filename, filesize, self.__host_id,
                                 client_id, curr_seq_num)
        packet_type_bytes = PacketType.METADATA.value.to_bytes(
            PACKET_TYPE_BYTES, ENDIANNESS)
        try:
            data_sender_sock.send(packet_type_bytes + metadata.get_bytes())
        except:
            Cli.print_log('\ntransmission interrupted', 'Error')
            return

        chunk = file_chunker.get_next_chunk()
        bytes_sent = 0
        start_time = time.time()

        while chunk != None:
            try:
                data_sender_sock.send(chunk)
                bytes_sent += len(chunk)
                upload_speed = self.__calc_speed(bytes_sent, start_time)

                Cli.print_progress_bar(bytes_sent, filesize, upload_speed)
                chunk = file_chunker.get_next_chunk()
            except:
                Cli.print_log('\ntransmission interrupted', 'Error')
                break

        file_chunker.close_file()
        data_sender_sock.close()

    def __update_recent_packets(self, src_id, seq_num, timestamp):
        now = time.time()
        for i in range(len(self.__recent_packets) - 1, -1, -1):
            if now - self.__recent_packets[i][2] > RECENT_PACKET_EXPIRATION:
                self.__recent_packets.pop(i)
        self.__recent_packets.append([src_id, seq_num, timestamp])

    def __calc_speed(self, bytes_cnt, start_time):
        current_time = time.time()
        speed = bytes_cnt / (current_time - start_time + EPSILON)

        if speed < 1000:
            return f'{speed} B/s'

        if speed < 1000 ** 2:
            return f'{speed / 1000:.2f} KB/s'

        if speed < 1000 ** 3:
            return f'{speed / (1000 ** 2):.2f} MB/s'

        if speed < 1000 ** 4:
            return f'{speed / (1000 ** 3):.2f} GB/s'

        return 'TOO FAST!'

    def __is_expired(self, timestamp, timeout):
        if timestamp == 0:
            return False
        return time.time() - timestamp > timeout
