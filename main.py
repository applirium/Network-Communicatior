import socket
import threading
import time
import binascii
import struct

FLAGS = {"SWITCH": 128, "FIN": 64, "KEEP": 32, "FILE": 16, "TXT": 8, "ERROR": 4, "ACK": 2, "INIT": 1}


class Sender:
    def __init__(self, switch=None):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                if switch is None:
                    self.ip = input("Sender IP: ")  # "127.0.0.1"
                    self.port = int(input("Sender port: "))  # 42069
                else:
                    self.ip = switch[0]
                    self.port = switch[1]

                self.sock.sendto(info_messages(["INIT"]), (self.ip, self.port))

                message, self.receiver = self.sock.recvfrom(1024)

                init_command = flag_check(message, ["INIT", "ACK"], ["FILE", "TXT"])

                if init_command is not None:
                    print(f"Client: Connection successfully established with server! {self.receiver[0]}:{self.receiver[1]}")
                    print("Client: Actions Client: Disconnect | Switch | Text | File | Help")

                self.thread_status = True
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
                self.sock.sendto(info_messages(["FIN"]), self.receiver)
                data = self.sock.recv(1024)

                end_command = flag_check(data, ["FIN", "ACK"])

                if end_command is not None:
                    self.thread_status = False
                    self.thread.join()
                    self.sock.close()
                    print(f"Client: Disconnected from server")
                    return None

            elif action == "text":
                self.sock.sendto(info_messages(["TXT", "INIT"]), self.receiver)
                data = self.sock.recv(1024)

                text_command = flag_check(data, ["TXT", "INIT", "ACK"])

                if text_command is not None:
                    print(f"Client: Sending text")

            elif action == "file":
                self.sock.sendto(info_messages(["FILE", "INIT"]), self.receiver)
                data = self.sock.recv(1024)

                file_command = flag_check(data, ["FILE", "INIT", "ACK"])

                if file_command is not None:
                    print(f"Client: Sending file")

            elif action == "switch":
                self.sock.sendto(info_messages(["SWITCH"]), self.receiver)
                data = self.sock.recv(1024)

                end_command = flag_check(data, ["SWITCH", "ACK"])

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
        while self.thread_status:
            try:
                self.sock.settimeout(5)

                self.sock.sendto(info_messages(["KEEP"]), self.receiver)
                data = self.sock.recv(1024)

                keep_request = flag_check(data, ["KEEP", "ACK"])

                if keep_request is not None:
                    print(f"Client: I am alive!")
                    time.sleep(5)

            except (TimeoutError, ConnectionResetError):
                print(f"Client: Connection was interrupted, press end to terminate program! ")
                return None


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

        self.sender = None

        print(f"Server: Server is up and running, listening to port {self.port}")

    def listen(self):
        while True:
            try:
                if self.sender is None:
                    self.sock.settimeout(60)
                else:
                    self.sock.settimeout(None)

                message, self.sender = self.sock.recvfrom(1024)

                init_request = flag_check(message, ["INIT"], ["FILE", "TXT"])
                keep_request = flag_check(message, ["KEEP"])
                file_request = flag_check(message, ["FILE", "INIT"], ["FIN"])
                txt_request = flag_check(message, ["TXT", "INIT"], ["FIN"])
                switch_request = flag_check(message, ["SWITCH"])
                end_request = flag_check(message, ["FIN"])

                if init_request is not None:
                    self.sock.sendto(info_messages(["INIT", "ACK"]), self.sender)
                    print(f"Server: Connection with client was successfully established! {self.sender[0]}:{self.sender[1]}")

                elif keep_request is not None:
                    self.sock.sendto(info_messages(["KEEP", "ACK"]), self.sender)
                    print(f"Server: Client is alive! ")

                elif file_request is not None:
                    self.sock.sendto(info_messages(["FILE", "INIT", "ACK"]), self.sender)
                    print(f"Server: Client is sending file! ")

                elif txt_request is not None:
                    self.sock.sendto(info_messages(["TXT", "INIT", "ACK"]), self.sender)
                    print(f"Server: Client is sending text! ")

                elif switch_request is not None:
                    self.sock.sendto(info_messages(["SWITCH", "ACK"]), self.sender)
                    print(f"Server: Switching with client! ")
                    self.sock.close()
                    return tuple((self.ip, self.port))

                elif end_request is not None:
                    self.sock.sendto(info_messages(["FIN", "ACK"]), self.sender)
                    print(f"Server: Client disconnected from server")
                    self.sender = None

            except TimeoutError:
                print("Server: Server connection timed out")
                return None


def flag_creation(*args):
    flag_sum = 0x00
    for i in args:
        flag_sum |= FLAGS[i]
    return flag_sum


def flag_decode(flags):
    list_of_flags = []

    for flag_name, flag_value in FLAGS.items():
        if flags & flag_value:
            list_of_flags.append(flag_name)

    return list_of_flags


def info_messages(flag, message=""):
    flags = flag_creation(*flag)
    header = struct.pack("!BHHH", flags, 0, 0, crc_creation(flags))
    return header + bytes(message, encoding="utf-8")


def crc_creation(flags):
    header = struct.pack("!BHH", flags, 0, 0)
    crc = binascii.crc_hqx(header, 0)
    return crc


def flag_check(message, flag, nflag=()):
    flag_code, length, seq, rec_crc = struct.unpack("!BHHH", message[0:7])
    flags = flag_decode(int(flag_code))
    flags_number = flag_creation(*flags)

    if crc_creation(flags_number) == rec_crc and all(pos_flag in flags for pos_flag in flag) and all(neg_flag not in flags for neg_flag in nflag):
        return str(message[7:], encoding="utf-8")
    else:
        return None


while True:
    msg = input("Receiver of Sender: ")
    if msg == "1":
        user = Sender()
        switch_status = user.request()

        while switch_status is not None:
            if msg == "1":
                user = Receiver(switch_status)
                switch_status = user.listen()
                msg = "2"
            else:
                time.sleep(5)
                user = Sender(switch_status)
                switch_status = user.request()
                msg = "1"

    elif msg == "2":
        user = Receiver()
        switch_status = user.listen()

        while switch_status is not None:
            if msg == "1":
                user = Receiver(switch_status)
                switch_status = user.listen()
                msg = "2"
            else:
                time.sleep(5)
                user = Sender(switch_status)
                switch_status = user.request()
                msg = "1"

    elif msg == "3":
        break
    else:
        print("Wrong input")
