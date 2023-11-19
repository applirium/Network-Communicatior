import socket
import common
import threading
import time


class Sender:
    def __init__(self) -> None:
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                common.SENDER_IP = "127.0.0.1"          # input("sender ip: ")
                common.SENDER_PORT = 42069              # int(input("sender port: "))

                self.sock.settimeout(60)
                self.receiver = None

                self.sock.sendto(common.info_messages(["INIT"]), (common.SENDER_IP, common.SENDER_PORT))
                message, self.receiver = self.sock.recvfrom(1024)

                if common.flag_check(message,"ACK"):
                    print(f"Connection successfully done {self.receiver}")
                    self.functionality()
            except TimeoutError:
                print("Client connection timed out")
                continue
            except ConnectionResetError:
                print("Server is not running")
                continue

    def functionality(self):
        while True:
            thread = threading.Thread(target=self.keep_alive)
            thread.daemon = True
            thread.start()

            action = input("Actions: Disconnect ").lower()
            if action == "disconnect":
                print(f"Client disconnected from server")
                break


    def receive(self):
        message, self.receiver = self.sock.recvfrom(1024)
        return str(message, encoding="utf-8")

    def send_message(self, message):
        self.sock.sendto(bytes(message, encoding="utf-8"), self.receiver_addr)

    def keep_alive(self):
        while True:
            self.sock.sendto(common.info_messages(["KEEP"]), self.receiver)
            data = self.sock.recv(1024)
            if common.flag_check(data,"KEEP"):
                print("Connection is working")
            else:
                print("Connection has ended")
                break
            time.sleep(5)

    def quit(self):
        self.sock.close()
        print("Client closed")


sender = Sender()
