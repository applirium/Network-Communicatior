import math
import random
import socket
import threading
from common import flag_check, packet_construct, fragment_size_check, mistake_rate_check, MAX_FRAGMENT
import time
import os


class Sender:
    def __init__(self, switch=None):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                if switch is None:
                    self.ip = "127.0.0.1"  # input("Sender IP: ")
                    self.port = 42069      # int(input("Sender port: "))
                else:
                    self.ip = switch[0]
                    self.port = switch[1]

                self.sock.sendto(packet_construct(["INIT"]), (self.ip, self.port))

                message, self.receiver = self.sock.recvfrom(MAX_FRAGMENT)

                _, init_command = flag_check(message, ["INIT", "ACK"], ["DATA"])

                if init_command is not None:
                    print(f"Client: Connection successfully established with server! {self.receiver[0]}:{self.receiver[1]}")
                    print("Client: Actions Client: Disconnect | Switch | Text | File | Help")

                self.thread_status = True
                self.keep_console = True

                self.thread = threading.Thread(target=self.keep_alive)
                self.thread.daemon = True
                self.thread.start()
                break

            except ConnectionResetError:
                print(f"Client: Server is not running")

    def request(self):
        while True:
            action = input().lower()

            if action == "disconnect":
                self.sock.sendto(packet_construct(["FIN"]), self.receiver)
                data = self.sock.recv(MAX_FRAGMENT)

                _, end_command = flag_check(data, ["FIN", "ACK"])

                if end_command is not None:
                    self.thread_status = False
                    self.thread.join()
                    self.sock.close()

                    print(f"Client: Disconnected from server")
                    return None

            elif action == "file" or action == "text":
                buffed_file = b""
                message = ""
                buffer_sent = []

                self.keep_console = False

                if action == "file":
                    while True:
                        try:
                            path = input("Client: Set name of a file: ")
                            absolute_path = os.path.abspath(path)
                            size = os.path.getsize(path)
                            file = open(absolute_path, "rb")
                            buffed_file = file.read()
                            file.close()

                            print(f"Client: File: {path} Size: {size} B Absolute path: {absolute_path}")
                            break

                        except FileNotFoundError:
                            print("Client: File not found")

                    fragment_size = fragment_size_check(size)
                    packet_transfer = math.ceil(size / fragment_size)

                    print(f"Client: Sending {packet_transfer} packets!")

                else:
                    path = ""
                    message = input("Client: Input message to send: ")
                    size = len(message)
                    fragment_size = fragment_size_check(size)
                    packet_transfer = math.ceil(size / fragment_size)

                    print(f"Client: Message: {message} Size: {size} B")
                    print(f"Client: Sending {packet_transfer} packets!")

                window_size = min(4, packet_transfer)
                buffer = list(range(packet_transfer))
                mistake_rate = mistake_rate_check()

                self.sock.sendto(packet_construct(["DATA", "INIT"], data=bytes(path, encoding="utf-8")), self.receiver)
                data = self.sock.recv(MAX_FRAGMENT)

                _, data_init_command = flag_check(data, ["DATA", "INIT", "ACK"])

                if data_init_command is not None:
                    self.thread_status = False
                    self.thread.join()

                while len(buffer) > 0 or len(buffer_sent) > 0:
                    while len(buffer_sent) < window_size and len(buffer) > 0:
                        fragment_size = min(size, fragment_size)

                        error_flag = random.random() < mistake_rate

                        if path == "":
                            data_to_send = bytes(message[fragment_size * buffer[0]: fragment_size * (buffer[0] + 1)], encoding='utf-8')
                        else:
                            data_to_send = buffed_file[fragment_size * buffer[0]: fragment_size * (buffer[0] + 1)]

                        packet_to_send = packet_construct(["DATA"], sequence_number=buffer[0], data=data_to_send, error=error_flag)

                        self.sock.sendto(packet_to_send, self.receiver)
                        buffer_sent.append(buffer.pop(0))

                    data = self.sock.recv(MAX_FRAGMENT)

                    seq_res, data_transfer_command = flag_check(data, ["DATA", "ACK"], ["INIT", "FIN", "ERROR"])
                    seq_err, data_transfer_error = flag_check(data, ["DATA", "ACK", "ERROR"], ["INIT", "FIN"])

                    if data_transfer_command is not None:
                        transfer_type = "Text" if path == "" else "File"
                        print(f"Client: {transfer_type} fragment {seq_res + 1} size: {fragment_size} B was sent successfully!")

                        size -= fragment_size
                        buffer_sent.remove(seq_res)

                    if data_transfer_error is not None:
                        seq_to_remove = buffer_sent.index(seq_err)
                        buffer.insert(0, buffer_sent.pop(seq_to_remove))

                        transfer_type = "Text" if path == "" else "File"
                        print(f"Client: {transfer_type} fragment {seq_err + 1} size: {fragment_size} B was fractured!")

                self.sock.sendto(packet_construct(["DATA", "FIN"]), self.receiver)
                data = self.sock.recv(MAX_FRAGMENT)

                _, data_end_command = flag_check(data, ["DATA", "FIN", "ACK"])

                if data_end_command is not None:
                    self.thread_status = True
                    self.keep_console = True

                    self.thread = threading.Thread(target=self.keep_alive)
                    self.thread.daemon = True
                    self.thread.start()

            elif action == "switch":
                self.sock.sendto(packet_construct(["INIT", "FIN"]), self.receiver)
                data = self.sock.recv(1024)

                _, end_command = flag_check(data, ["INIT", "FIN", "ACK"])

                if end_command is not None:
                    self.thread_status = False
                    self.thread.join()
                    self.sock.close()

                    print(f"Client: Switching with server!")
                    return tuple((self.ip, self.port))

            elif action == "end":
                return None

            else:
                print("Client: Invalid input")

    def keep_alive(self):
        not_responding = 0

        while self.thread_status:
            try:
                self.sock.settimeout(5)

                self.sock.sendto(packet_construct(["KEEP"]), self.receiver)
                data = self.sock.recv(MAX_FRAGMENT)

                _, keep_request = flag_check(data, ["KEEP", "ACK"])

                if keep_request is not None:
                    if self.keep_console:
                        print(f"Client: I am alive!")

                    not_responding = 0
                    time.sleep(5)

            except (TimeoutError, ConnectionResetError):
                not_responding += 1
                if not_responding < 4:
                    print(f"Client: Server is not responding! ")
                    time.sleep(5)
                else:
                    print(f"Client: Connection was interrupted, press end to terminate program! ")
                    return None
