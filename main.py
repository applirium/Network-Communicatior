import socket
import threading
import time
import binascii
import struct

FLAGS = {"FIN": 32, "KEEP": 16, "DATA": 8, "ERROR": 4, "ACK": 2, "INIT": 1}


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

                self.sock.sendto(info_messages(["INIT"]), (self.ip, self.port))

                message, self.receiver = self.sock.recvfrom(1024)

                init_command = flag_check(message, ["INIT", "ACK"], ["DATA"])

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

            elif action == "file" or action == "text":
                self.sock.sendto(info_messages(["DATA", "INIT"]), self.receiver)
                data = self.sock.recv(1024)

                data_command = flag_check(data, ["DATA", "INIT", "ACK"])

                if data_command is not None:
                    print(f"Client: Sending something")

            elif action == "switch":
                self.sock.sendto(info_messages(["INIT", "FIN"]), self.receiver)
                data = self.sock.recv(1024)

                end_command = flag_check(data, ["INIT", "FIN", "ACK"])

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

                self.sock.sendto(info_messages(["KEEP"]), self.receiver)
                data = self.sock.recv(1024)

                keep_request = flag_check(data, ["KEEP", "ACK"])

                if keep_request is not None:
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


class Receiver:
    def __init__(self, switch=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if switch is None:
            self.ip = "127.0.0.1"  # socket.gethostbyname(socket.gethostname)
            self.port = 42069  # int(input("Insert port number: "))
            self.sock.bind((self.ip, self.port))
        else:
            self.ip = "127.0.0.1"  # socket.gethostbyname(socket.gethostname)
            self.port = switch[1]
            self.sock.bind(switch)

        self.connected = False
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

                init_request = flag_check(message, ["INIT"], ["FIN", "DATA", "ACK"])
                keep_request = flag_check(message, ["KEEP"])
                data_request = flag_check(message, ["DATA", "INIT"], ["FIN", "ACK"])
                switch_request = flag_check(message, ["INIT", "FIN"])
                end_request = flag_check(message, ["FIN"], ["INIT", "DATA", "ACK"])

                if init_request is not None:
                    self.sock.sendto(info_messages(["INIT", "ACK"]), self.sender)
                    self.connected = True
                    print(f"Server: Connection with client was successfully established! {self.sender[0]}:{self.sender[1]}")

                elif keep_request is not None:
                    if self.connected is False:
                        print(f"Server: Connection with client was successfully reestablished! {self.sender[0]}:{self.sender[1]}")
                        self.connected = True

                    self.sock.sendto(info_messages(["KEEP", "ACK"]), self.sender)
                    print(f"Server: Client is alive! ")

                elif data_request is not None:
                    self.sock.sendto(info_messages(["DATA", "INIT", "ACK"]), self.sender)
                    print(f"Server: Client is sending something! ")

                elif switch_request is not None:
                    self.sock.sendto(info_messages(["INIT", "FIN", "ACK"]), self.sender)
                    print(f"Server: Switching with client! ")
                    self.sock.close()
                    return tuple((self.ip, self.port))

                elif end_request is not None:
                    self.sock.sendto(info_messages(["FIN", "ACK"]), self.sender)
                    print(f"Server: Client disconnected from server")
                    self.sender = None

            except TimeoutError:
                self.sock.close()
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
