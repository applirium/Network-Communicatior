import os.path
import socket
from common import flag_check, packet_construct, MAX_FRAGMENT, HEADER_SIZE
import struct
import binascii
import time


class Receiver:
    def __init__(self, switch=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if switch is None:
            self.ip = "127.0.0.1"  # socket.gethostbyname(socket.gethostname)
            self.port = int(input("Insert port number: "))  # 42069
            self.sock.bind((self.ip, self.port))
        else:
            self.ip = "127.0.0.1"  # socket.gethostbyname(socket.gethostname)
            self.port = switch[1]
            self.sock.bind(switch)

        self.connected = False
        self.sender = None

        print(f"Server: Server is up and running, listening to port {self.port}")

    def listen(self):
        file_name = ""
        data = []
        fragment_position = []

        success = 0
        fail = 0
        start_time = 0
        size = 0

        while True:
            try:
                if self.sender is None:
                    self.sock.settimeout(60)
                else:
                    self.sock.settimeout(None)

                message, self.sender = self.sock.recvfrom(MAX_FRAGMENT + HEADER_SIZE)

                _, init_request = flag_check(message, ["INIT"], ["FIN", "DATA", "ACK"])
                _, keep_request = flag_check(message, ["KEEP"])
                _, data_init_request = flag_check(message, ["DATA", "INIT"], ["FIN", "ACK"])
                seq_data, data_transition_request = flag_check(message, ["DATA"], ["INIT", "FIN", "ACK"])
                _, data_end_request = flag_check(message, ["DATA", "FIN"], ["INIT", "ACK"])
                _, switch_request = flag_check(message, ["INIT", "FIN"])
                _, end_request = flag_check(message, ["FIN"], ["INIT", "DATA", "ACK"])

                if init_request is not None:
                    self.sock.sendto(packet_construct(["INIT", "ACK"]), self.sender)
                    self.connected = True
                    print(f"Server: Connection with client was successfully established! {self.sender[0]}:{self.sender[1]}")

                elif keep_request is not None:
                    if self.connected is False:
                        self.connected = True
                        print(f"Server: Connection with client was successfully reestablished! {self.sender[0]}:{self.sender[1]}")

                    self.sock.sendto(packet_construct(["KEEP", "ACK"]), self.sender)
                    print(f"Server: Client is alive! ")

                elif data_init_request is not None:
                    string = str(data_init_request, encoding="utf-8")
                    file_name, size = string.split(",")
                    size = int(size)

                    self.sock.sendto(packet_construct(["DATA", "INIT", "ACK"]), self.sender)

                elif data_transition_request is not None:
                    if start_time == 0:
                        start_time = time.time()

                    _, _, rec_crc = struct.unpack("!BHH", message[0:5])
                    if rec_crc == binascii.crc_hqx(data_transition_request, 0):
                        self.sock.sendto(packet_construct(["DATA", "ACK"], sequence_number=seq_data), self.sender)

                        if file_name == '':
                            data_transition_request = str(data_transition_request, encoding='utf-8')

                        print(f"Server: {'Text' if file_name == '' else 'File'} fragment {seq_data + 1} was received successfully: {data_transition_request}")

                        data.append(data_transition_request)
                        fragment_position.append(seq_data + 1)
                        success += 1
                    else:
                        self.sock.sendto(packet_construct(["DATA", "ACK", "ERROR"], sequence_number=seq_data), self.sender)
                        fail += 1

                elif data_end_request is not None:
                    self.sock.sendto(packet_construct(["DATA", "FIN", "ACK"]), self.sender)

                    pair = sorted(list(zip(fragment_position, data)), key=lambda x: x[0])
                    _, num = zip(*pair)
                    stop_time = time.time()

                    if file_name == "":
                        final_message = "".join(num)
                        print(f"Server: Client sent message: {final_message}")

                    else:
                        index = 1
                        while os.path.exists(file_name):
                            if index == 1:
                                file_name = file_name.replace(".", f"({index}).", 1)
                            else:
                                file_name = file_name.replace(f"({index-1}).", f"({index}).", 1)
                            index += 1

                        with open(file_name, 'wb') as file:
                            file.writelines(num)

                        print(f"Server: Client sent file: {file_name}")

                    transmission_time = stop_time - start_time

                    print(f"Total fragments: {success} Fragments retransmitted: {fail}")
                    print(f"Time of transmission: {round(transmission_time,3)} s Speed of transmission: {round(size / (transmission_time * 1000000),3)} MB/s")

                    data = []
                    fragment_position = []
                    start_time = 0
                    success = 0
                    fail = 0

                elif switch_request is not None:
                    self.sock.sendto(packet_construct(["INIT", "FIN", "ACK"]), self.sender)
                    print(f"Server: Switching with client! ")
                    self.sock.close()
                    return tuple((self.ip, self.port))

                elif end_request is not None:
                    self.sock.sendto(packet_construct(["FIN", "ACK"]), self.sender)
                    print(f"Server: Client disconnected from server")
                    self.sender = None

            except TimeoutError:
                self.sock.close()
                print("Server: Server connection timed out")
                return None
