import os
import configparser
import random
import threading
import time

from collections import defaultdict
from difflib import SequenceMatcher
from netifaces import interfaces, ifaddresses, AF_INET
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, \
    SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, timeout
from threading import Thread

from chunk_manager.file_chunker import FileChunker
from messages.ack import Ack
from messages.discovery import Discovery
from messages.offer import Offer
from messages.packet_type import PacketType
from ui.Cli import Cli
from status.status import Status

FILENAME_LENGTH_BYTES = 2
PACKET_TYPE_BYTES = 1
ENDIANNESS = 'little'

BROADCAST_ADDR = '<broadcast>'
BROADCAST_PORT = 12345
# TX_PORT = 7337
RX_PORT = 3773

RX_REPO_PATH = './repository/rx'
TX_REPO_PATH = './repository/tx'

TRANSMISSION_TIMEOUT = 1  # seconds
OFFER_TIMEOUT = 2  # seconds
DATA_TRANSFER_TIMEOUT = 5  # seconds

MIN_PORT = 1024
MAX_PORT = 65535

SIMILARITY_THRESHOLD = 0.5
TOPOLOGY_CONFIG_PATH = './topology.conf'
BACKLOG_COUNT = 5
BROADCAST_ID = -1

class P2PFileSharing:
    def __init__(self, chunck_size=10000):
        self.chunk_size = chunck_size  # Bytes

        self.__tx_sock = socket(AF_INET, SOCK_STREAM)

        self.__rx_sock = socket(AF_INET, SOCK_STREAM)
        self.__rx_sock.bind(('', RX_PORT))

        self.__routing_dict = dict()
        self.__routing_dict_lock = threading.Lock()

        self.__offers_dict = dict()

        self.__discovery_sock = None
        self.__offerer_sock = socket(AF_INET, SOCK_DGRAM)
        self.__data_receiver_sock = None
        # self.data_sender_sock = None
        self.__listener_sock = socket(AF_INET, SOCK_DGRAM)
        self.__listener_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.__listener_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.__listener_sock.bind(('', BROADCAST_PORT))

        # read from conf file
        config = configparser.ConfigParser()
        config.read(TOPOLOGY_CONFIG_PATH)
        self.__host_id = int(config['Self']['HOST_ID'].replace(' ', ''))
        self.__neighbour_ips = config['Neighbours']['HOST_IPS'].replace(' ', '').split(',')
        self.__neighbour_ids = list(map(int, config['Neighbours']['HOST_IDS'].replace(' ', '').split(',')))
        # print(self.__neighbour_ips)
        # print(self.__neighbour_ids)

        self.__seq_num = random.randint(0, 2**32-1)
        self.__seq_num_lock = threading.Lock()

        Thread(target=self.__receive).start()
        # Thread(target=self.__get_ack).start()

    def request_file(self):
        Cli.print_log('enter your query:', 'Info')
        req_filename = input()
        Cli.print_log('LOG: request_file(' + req_filename + ')', 'Debug')
        self.__send_discovery(req_filename)

        # offers = self.__get_offers()
        Cli.show_offers(offers)

        if len(offers) == 0:
            return Status.NO_OFFERS

        choice = Cli.choose_offer(offers)
        if choice == None:
            return Status.NO_CHOICE

        self.__send_ack(choice)

        filename = choice[1]['name']
        filesize = choice[1]['size']
        status = self.__receive_data(filename, filesize)

        return status

    def __send_discovery(self, req_filename):
        Cli.print_log('LOG: __send_discovery(' + req_filename + ')', 'Debug')

        # TODO: send to all neighbours, set a valid seq number
        with self.__seq_num_lock:
            curr_seq_num = self.__seq_num
            self.__seq_num += 1
        discovery = Discovery()
        discovery.set_packet_data(
            req_filename, self.__host_id, BROADCAST_ID, curr_seq_num)
        for neighbour in self.__neighbour_ips:
            Thread(target=self.__send_discovery_to_neighbour, args=(discovery, neighbour))

    def __send_discovery_to_neighbour(self, discovery_packet, neighbour_ip):
        discovery_sock = socket(AF_INET, SOCK_STREAM)
        discovery_sock.setblocking(0)
        discovery_sock.connect((neighbour_ip, RX_PORT))

        packet_type_bytes = PacketType.DISCOVERY.value.to_bytes(PACKET_TYPE_BYTES, ENDIANNESS)
        discovery_sock.send(packet_type_bytes + discovery_packet)

        discovery_sock.close()

    def __receive(self):
        Cli.print_log('LOG: __listen()', 'Debug')

        self.__rx_sock.listen(BACKLOG_COUNT)
        # self.rx_sock.setblocking(0)

        while True:
            sock, sender_addr = self.__rx_sock.accept()
            sock.settimeout(DATA_TRANSFER_TIMEOUT)
            Thread(target=self.__handle_connection,
                   args=(sock, sender_addr)).start()

    def __handle_connection(self, rec_sock, sender_addr):
        buff = b''

        while len(buff) < 9:
            buff += rec_sock.recv(self.chunk_size)

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
        # TODO
        # elif packet_type == PacketType.DATA.value:
        #     p = 
        else:
            rec_sock.close()
            return

        if dst_host_id != self.__host_id and packet_type != PacketType.DISCOVERY.value:
            self.__redirect_packet(p, buff, dst_host_id, rec_sock)
            rec_sock.close()
        else:
            while True:
                try:
                    p.set_bytes(buff)
                    break
                except:
                    buff += rec_sock.recv(self.chunk_size)
            rec_sock.close()

            self.__process_packet(p, packet_type, src_host_id, sender_addr[0])
            
    def __redirect_packet(self, packet, buff, dst_host_id, rec_sock):
        if dst_host_id not in self.__routing_dict:
            return

        send_sock = socket(AF_INET, SOCK_STREAM)
        send_sock.connect((self.__routing_dict[dst_host_id], RX_PORT))
        send_sock.setblocking(0)
        send_sock.settimeout(DATA_TRANSFER_TIMEOUT)
        cursor = 0
        while True:
            send_sock.send(buff[cursor:])
            cursor += len(buff)
            try:
                packet.set_bytes(buff)
                return
            except:
                buff += rec_sock.recv(self.chunk_size)

    def __process_packet(self, packet, packet_type, src_host_id, sender_ip):
        if packet_type == PacketType.DISCOVERY.value:
            self.__send_offer(packet.get_filename(), src_host_id, (self.__routing_dict[src_host_id], RX_PORT))
            for neighbour in self.__neighbour_ips:
                if neighbour != sender_ip:
                    Thread(target=self.__send_discovery_to_neighbour(packet, neighbour))
        elif packet_type == PacketType.OFFER.value:
            self.__offers_dict[packet.get_src_host_id] = packet.get_matching_files()
        elif packet_type == PacketType.ACK.value:
            # FIXME
            self.__send_data(packet.get_filename, (self.__routing_dict[src_host_id], RX_PORT))
        # TODO
        # elif packet_type == PacketType.DATA.value:
        #     p = 




    # def __listen(self):
    #     Cli.print_log('LOG: __listen()', 'Debug')
    #     buffer = defaultdict(bytes)
    #     timestamps = defaultdict(int)
    #     current_client = None

    #     self.rx_sock.listen(BACKLOG_COUNT)
    #     self.rx_sock.setblocking(0)
    #     self.rx_sock.settimeout(DATA_TRANSFER_TIMEOUT)

    #     while True:
    #         try:
    #             sock, client = self.rx_sock.accept()
    #         except:
    #             return Status.TRANSFER_INTERRUPTED
    #         sock.setblocking(0)
    #         sock.settimeout(DATA_TRANSFER_TIMEOUT)

    #         if current_client is None:
    #             # rec_bytes, client = self.__listener_sock.recvfrom(
    #             #     self.chunk_size)
    #             rec_bytes = sock.recv(self.chunk_size)

    #             if self.__is_myself(client):
    #                 continue

    #             if timestamps[client] == 0:
    #                 timestamps[client] = time.time()
    #             buffer[client] += rec_bytes
    #             current_client = client

    #         else:
    #             discovery = Discovery()
    #             try:
    #                 # The following line may raise an exception
    #                 discovery.set_bytes(buffer[current_client])
    #                 self.__send_offer(discovery.get_filename(
    #                 ), discovery.get_src_host_id(), current_client)
    #             except ValueError:
    #                 if not self.__is_expired(timestamps[current_client],
    #                                          TRANSMISSION_TIMEOUT):
    #                     rec_bytes, client = self.__listener_sock.recvfrom(
    #                         self.chunk_size)
    #                     if self.__is_myself(client):
    #                         continue

    #                     if timestamps[client] == 0:
    #                         timestamps[client] = time.time()
    #                     buffer[client] += rec_bytes
    #                     continue
    #             finally:
    #                 del buffer[current_client]
    #                 del timestamps[current_client]

    #                 if len(list(buffer.keys())) > 0:
    #                     current_client = list(buffer.keys())[0]
    #                 else:
    #                     current_client = None
    
    
    # FIXME
    def __send_offer(self, req_filename, dst_host_id, client):
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

        # offer = Offer(matching_files=matching_files)
        # TODO: set valid seq number
        offer = Offer()
        offer.set_packet_data(matching_files, self.__host_id, dst_host_id, 0)

        # for test
        # new_offer = Offer()
        # b = offer.get_bytes()
        # new_offer.set_bytes(b)
        # print('src_offer: ', new_offer.get_src_host_id())
        # print('dst_offer: ', new_offer.get_dst_host_id())
        # print('seq_offer: ', new_offer.get_seq_num())
        # print('matched_offer: ', new_offer.get_matching_files())

        self.__offerer_sock.sendto(offer.get_bytes(), client)
        # ack = self.__get_ack(client)

    def __get_offers(self):
        Cli.print_log('LOG: __get_offers()', 'Debug')

        start_time = time.time()

        offers = {}
        buffer = defaultdict(bytes)
        timestamps = defaultdict(int)
        current_offerer = None

        while not self.__is_expired(start_time, OFFER_TIMEOUT):
            if current_offerer is None:
                try:
                    rec_bytes, offerer = self.__discovery_sock.recvfrom(
                        self.chunk_size)
                except:
                    continue
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
                        try:
                            rec_bytes, offerer = self.__discovery_sock.recvfrom(
                                self.chunk_size)
                        except:
                            continue
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
        Cli.print_log('LOG: __send_ack(' + str(choice) + ')', 'Debug')
        offerer, dic = choice
        filename = dic['name']
        while True:
            try:
                port_number = random.randint(MIN_PORT, MAX_PORT)
                self.__data_receiver_sock = socket(AF_INET, SOCK_STREAM)
                self.__data_receiver_sock.bind(('', port_number))
                break
            except OSError:
                pass

        ack = Ack()
        ack.set_data(filename, port_number)
        self.__discovery_sock.sendto(ack.get_bytes(), offerer)

        self.__discovery_sock.close()
        self.__discovery_sock = None

    def __get_ack(self):
        Cli.print_log('LOG: __get_ack()', 'Debug')

        buffer = defaultdict(bytes)
        timestamps = defaultdict(int)
        current_client = None

        while True:
            if current_client is None:
                rec_bytes, client = self.__offerer_sock.recvfrom(
                    self.chunk_size)
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
                    Thread(target=self.__send_data,
                           args=(filename, final_addr)).start()
                except ValueError:
                    if not self.__is_expired(timestamps[current_client],
                                             TRANSMISSION_TIMEOUT):
                        rec_bytes, client = self.__offerer_sock.recvfrom(
                            self.chunk_size)
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
        Cli.print_log('LOG: __send_data(' + filename +
                      ', ' + str(client) + ')', 'Debug')

        data_sender_sock = socket(AF_INET, SOCK_STREAM)
        data_sender_sock.connect(client)
        data_sender_sock.setblocking(0)
        data_sender_sock.settimeout(DATA_TRANSFER_TIMEOUT)

        file_chunker = FileChunker(
            os.path.join(TX_REPO_PATH, filename), self.chunk_size)

        filesize = file_chunker.get_file_size()

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
        data_sender_sock = None

    def __receive_data(self, filename, filesize):
        Cli.print_log('LOG: __receive_data(' + filename +
                      ', ' + str(filesize) + ')', 'Debug')

        self.__data_receiver_sock.listen(1)
        self.__data_receiver_sock.setblocking(0)
        self.__data_receiver_sock.settimeout(DATA_TRANSFER_TIMEOUT)
        try:
            sock, _ = self.__data_receiver_sock.accept()
        except:
            return Status.TRANSFER_INTERRUPTED
        sock.setblocking(0)
        sock.settimeout(DATA_TRANSFER_TIMEOUT)

        f = open(os.path.join(RX_REPO_PATH, filename), 'wb')
        written_bytes = 0
        status = Status.SUCCESS
        start_time = time.time()
        timer_start_time = start_time

        while written_bytes < filesize:
            try:
                buffer = sock.recv(self.chunk_size)
                if len(buffer) > 0:
                    timer_start_time = time.time()
                if self.__is_expired(timer_start_time, DATA_TRANSFER_TIMEOUT):
                    raise timeout
            except timeout:
                status = Status.TRANSFER_INTERRUPTED
                Cli.print_log('')
                break

            f.write(buffer)
            written_bytes += len(buffer)
            download_speed = self.__calc_speed(written_bytes, start_time)

            Cli.print_progress_bar(written_bytes, filesize, download_speed)

        f.close()
        self.__data_receiver_sock.close()
        self.__data_receiver_sock = None

        return status

    def __calc_speed(self, bytes_cnt, start_time):
        current_time = time.time()
        speed = bytes_cnt / (current_time - start_time)

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

    def __is_myself(self, client):
        if self.__discovery_sock == None:
            return False

        myPort = self.__discovery_sock.getsockname()[1]
        if client[0] in self.__get_host_ips() and client[1] == myPort:
            return True
        else:
            return False

    def __get_host_ips(self):
        if_ips = []
        for ifaceName in interfaces():
            address = [i['addr'] for i in ifaddresses(
                ifaceName).setdefault(AF_INET, [{'addr': 'No IP addr'}])]
            if_ips += address

        return if_ips
