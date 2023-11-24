import socket
from common import flag_check, info_messages


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
