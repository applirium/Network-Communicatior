import socket
import common
import threading
import time

class Sender:
    def __init__(self) -> None:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            common.SENDER_IP = "127.0.0.1"          # input("sender ip: ")
            common.SENDER_PORT = 42069              # int(input("sender port: "))

            self.receiver = None
            self.connected = False
            self.name = input("Insert your name: ")
            self.functionality()

        except ConnectionResetError:
            print("Server is not running")

    def functionality(self):
        thread = None
        while True:
            try:
                self.sock.settimeout(60)

                if not self.connected:
                    self.sock.sendto(common.info_messages(["INIT"], self.name), (common.SENDER_IP, common.SENDER_PORT))
                    message, self.receiver = self.sock.recvfrom(1024)

                    init_command = common.flag_check(message, ["INIT", "ACK"], ["FILE", "TXT"])

                    if init_command is not None:
                        print(f"{self.name}: Connection successfully done ")

                    self.connected = True
                    thread = threading.Thread(target=self.keep_alive)
                    thread.daemon = True
                    thread.start()

                action = input("Actions: Disconnect | Keep | Text | File | Help \n").lower()
                if action == "disconnect":
                    self.sock.sendto(common.info_messages(["FIN"]), self.receiver)
                    data = self.sock.recv(1024)

                    end_command = common.flag_check(data, ["FIN", "ACK"])

                    if end_command is not None:
                        self.connected = False
                        # thread.join()
                        self.sock.close()
                        print(f"{self.name}: Disconnected from server")
                        return

                elif action == "text":
                    self.sock.sendto(common.info_messages(["TXT"]), self.receiver)
                    data = self.sock.recv(1024)

                    text_command = common.flag_check(data, ["TXT", "ACK"])

                    if text_command is not None:
                        print(f"Client {self.name} sending text")

                elif action == "file":
                    self.sock.sendto(common.info_messages(["FILE"]), self.receiver)
                    data = self.sock.recv(1024)

                    file_command = common.flag_check(data, ["FILE", "ACK"])

                    if file_command is not None:
                        print(f"Client {self.name} sending file")

                elif action == "keep":
                    pass

                else:
                    print("Invalid input")

            except TimeoutError:
                print("Client connection timed out")
                break

    def keep_alive(self):
        while self.connected:
            try:
                self.sock.sendto(common.info_messages(["KEEP"]), self.receiver)
                data = self.sock.recv(1024)

                keep_request = common.flag_check(data, ["KEEP", "ACK"])

                if keep_request is not None:
                    self.sock.settimeout(60)
                    print(f"{self.name}: I am alive!")

                time.sleep(5)
            except TimeoutError:
                print(f"{self.name}: Connection has ended")
                break


while True:
    sender = Sender()
