import socket
import threading
from common import flag_check, info_messages
import time


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
                    self.keep_console = False

                    window_size = 4
                    fragment_size = int(input("Client: Max fragment size: "))

                    print(f"Client: Sending something")

                self.keep_console = True

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