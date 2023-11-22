import socket
import threading
import time
import binascii
import struct
import pyautogui
FLAGS = {"SWITCH": 128, "FIN": 64, "KEEP": 32, "FILE": 16, "TXT": 8, "ERROR": 4, "ACK": 2, "INIT": 1}


class Sender:
    def __init__(self) -> None:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sender_ip = "127.0.0.1"          # input("sender ip: ")
            sender_port = 42069              # int(input("sender port: "))

            self.receiver = None
            self.name = input("Insert your name: ")

            self.sock.sendto(info_messages(["INIT"], self.name), (sender_ip, sender_port))
            message, self.receiver = self.sock.recvfrom(1024)

            init_command = flag_check(message, ["INIT", "ACK"], ["FILE", "TXT"])

            if init_command is not None:
                print(f"{self.name}: Connection successfully established! {self.receiver[0]}:{self.receiver[1]}")
                print("Actions Client: Disconnect | Keep Off/On | Keep Text Off/On | Switch | Text | File | Help")

            self.connected = True
            self.keep = True
            self.keep_text = True

            self.thread = threading.Thread(target=self.keep_alive)
            self.thread.daemon = True
            self.thread.start()

            self.request()

        except ConnectionResetError:
            print(f"{self.name}: Server is not responding")

    def request(self):
        while self.thread.is_alive():
            action = input().lower()

            if action == "disconnect":
                self.sock.sendto(info_messages(["FIN"]), self.receiver)
                data = self.sock.recv(1024)

                end_command = flag_check(data, ["FIN", "ACK"])

                if end_command is not None:
                    self.connected = False
                    self.sock.close()
                    print(f"{self.name}: Disconnected from server")
                    return

            elif action == "text":
                self.sock.sendto(info_messages(["TXT"]), self.receiver)
                data = self.sock.recv(1024)

                text_command = flag_check(data, ["TXT", "ACK"])

                if text_command is not None:
                    print(f"{self.name}: Sending text")

            elif action == "file":
                self.sock.sendto(info_messages(["FILE"]), self.receiver)
                data = self.sock.recv(1024)

                file_command = flag_check(data, ["FILE", "ACK"])

                if file_command is not None:
                    print(f"{self.name}: Sending file")

            elif action == "switch":
                pass

            elif action == "keep off":
                self.keep = False
                print(f"{self.name}: Setting keep-alive OFF")

            elif action == "keep on":
                self.keep = True
                print(f"{self.name}: Setting keep-alive ON")

            elif action == "keep text off":
                self.keep_text = False
                print(f"{self.name}: Setting keep-alive prints OFF")

            elif action == "keep text on":
                self.keep_text = True
                print(f"{self.name}: Setting keep-alive prints ON")

            else:
                print("Invalid input")

    def keep_alive(self):
        while True:
            if self.keep is True:
                self.sock.sendto(info_messages(["KEEP"]), self.receiver)
                data = self.sock.recv(1024)

                keep_request = flag_check(data, ["KEEP", "ACK"])

                if keep_request is not None:
                    if self.keep_text:
                        print(f"{self.name}: I am alive!")

                    self.sock.settimeout(5)
            else:
                pyautogui.write("disconnect")
                pyautogui.press('enter')
                return

            time.sleep(5)

class Receiver:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver_port = 42069    # int(input("port number: "))

        self.sock.bind(("", receiver_port))
        self.senders = {}

        print(f"Server is up and running, listening to port {receiver_port}")
        self.listen()

    def listen(self):
        while True:
            try:
                if len(self.senders) == 0:
                    self.sock.settimeout(60)
                else:
                    self.sock.settimeout(None)

                message, sender = self.sock.recvfrom(1024)

                init_request = flag_check(message, ["INIT"], ["FILE", "TXT"])
                keep_request = flag_check(message, ["KEEP"])
                file_request = flag_check(message, ["FILE"])
                txt_request = flag_check(message, ["TXT"])
                listen_request = flag_check(message, ["SWITCH"])
                end_request = flag_check(message, ["FIN"])

                if init_request is not None:
                    self.senders[sender] = init_request

                    self.sock.sendto(info_messages(["INIT", "ACK"]), sender)
                    print(f"{self.senders[sender]}: Connection successfully established! {sender[0]}:{sender[1]}")
                    print(f"Number of connections: {len(self.senders)}")

                elif keep_request is not None:

                    self.sock.sendto(info_messages(["KEEP", "ACK"]), sender)
                    print(f"{self.senders[sender]}: Is alive! ")

                elif file_request is not None:
                    pass

                elif txt_request is not None:
                    pass

                elif listen_request is not None:

                    self.sock.sendto(info_messages(["SWITCH", "ACK"]), sender)

                elif end_request is not None:

                    self.sock.sendto(info_messages(["FIN", "ACK"]), sender)
                    print(f"{self.senders[sender]}: Disconnected from server")

                    self.senders.pop(sender)
                    print(f"Number of connections: {len(self.senders)}")

            except TimeoutError:
                print("Server was terminated")
                return


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
        client = Sender()
        break
    elif msg == "2":
        server = Receiver()
        break
    else:
        print("Wrong input")
