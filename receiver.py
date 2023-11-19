import socket
import common
import struct
import binascii


class Receiver:
    def __init__(self) -> None:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            common.RECEIVER_IP = "127.0.0.1"
            common.RECEIVER_PORT = 42069    # int(input("port number: "))

            self.sock.bind(("", common.RECEIVER_PORT))
            self.sock.settimeout(60)
            self.sender = None

            print(f"Server is up and running, listening to port {common.RECEIVER_PORT}")

            message, self.sender = self.sock.recvfrom(1024)
            self.sock.sendto(common.info_messages(["INIT"]), self.sender)

            print(f"Connection successfully done {self.sender}")
            self.functionality()
        except TimeoutError:
            print("Server connection timed out")

    def functionality(self):
        while True:

            action = input("Actions: Disconnect | Switch ").lower()
            if action == "disconnect":
                print(f"Client disconnected from server")
                break
            elif action == "switch":
                pass
            else:
                pass

    def receive_message(self):
        message = None
        while message is None:
            message, self.sender = self.sock.recvfrom(1024)

        return str(message, encoding="utf-8")

    def send_response(self):
        self.sock.sendto(b"Message received", self.sender)

    def send_last_response(self):
        self.sock.sendto(b"End connection", self.sender)

    def quit(self):
        self.sock.close()
        print("Server closed")


receiver = Receiver()
