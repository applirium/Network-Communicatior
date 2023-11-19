import socket
import common


class Receiver:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        common.RECEIVER_IP = "127.0.0.1"
        common.RECEIVER_PORT = 42069    # int(input("port number: "))

        self.sock.bind(("", common.RECEIVER_PORT))
        self.senders = {}

        print(f"Server is up and running, listening to port {common.RECEIVER_PORT}")
        self.functionality()

    def functionality(self):
        while True:
            try:
                if len(self.senders) == 0:
                    self.sock.settimeout(60)
                else:
                    self.sock.settimeout(None)

                message, sender = self.sock.recvfrom(1024)

                init_request = common.flag_check(message, ["INIT"], ["FILE", "TXT"])
                keep_request = common.flag_check(message, ["KEEP"])
                file_request = common.flag_check(message, ["FILE"])
                txt_request = common.flag_check(message, ["TXT"])
                end_request = common.flag_check(message, ["FIN"])

                if init_request is not None:
                    self.senders[sender] = init_request

                    self.sock.sendto(common.info_messages(["INIT", "ACK"]), sender)
                    print(f"{self.senders[sender]}: Connection successfully done")

                elif keep_request is not None:

                    self.sock.sendto(common.info_messages(["KEEP", "ACK"]), sender)
                    print(f"{self.senders[sender]}: Is alive! ")

                elif file_request is not None:
                    pass

                elif txt_request is not None:
                    pass

                elif end_request is not None:

                    self.sock.sendto(common.info_messages(["FIN", "ACK"]), sender)
                    print(f"{self.senders[sender]}: Disconnected from server")

                    self.senders.pop(sender)

            except TimeoutError:
                print("Server connection timed out")
                break

    def input(self):
        while True:
            action = input("Actions: Disconnect | Switch ").lower()
            if action == "disconnect":
                for sender, name in self.senders:
                    self.sock.sendto(common.info_messages(["FIN"]), sender)

                    message, sender = self.sock.recvfrom(1024)
                    if common.flag_check(message, ["FIN", "ACK"]) and name not in self.senders:
                        print(f"Client {name} has been disconnected")

                self.sock.close()
                print(f"Server disconnected")
            elif action == "switch":
                name = None

                while name not in self.senders:
                    name = input("With what client do you want to switch: ")

                self.sock.sendto(common.info_messages(["SWITCH"]), sender)

            else:
                print("Invalid action")


receiver = Receiver()
