import os.path
import socket
from common import flag_check, packet_construct, rounder, extract_bits_from_header, MAX_FRAGMENT, HEADER_SIZE
import binascii
import time


class Receiver:
    def __init__(self, switch=None):                                             # Initializing the Receiver class
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if switch is None:                                                       # If switch is None, bind to a port entered by the user, else bind to the provided switch port
            self.ip = socket.gethostbyname(socket.gethostname())                 # Get the local IP address
            self.port = int(input("Insert port number: "))                       # Get user input for port number
            self.sock.bind((self.ip, self.port))
        else:
            self.ip = socket.gethostbyname(socket.gethostname())
            self.port = switch
            self.sock.bind((self.ip, self.port))

        self.connected = False                                                   # Flag to indicate connection status
        self.sender = None                                                       # Variable to store sender's address

        print(f"Server: Server is up and running, listening on {self.ip}:{self.port}")

    def listen(self):                                                           # Function handling server listening and it's answering to clients requests
        file_name = ""                                                          # Initialization of variables used in the listening loop
        data = []
        fragment_position = []

        success = 0
        fail = 0
        start_time = 0
        size = 0

        while True:
            try:
                if self.sender is None:                                         # Set timeout for receiving data if self.sender is None - initial connection
                    self.sock.settimeout(60)
                else:
                    self.sock.settimeout(None)

                message, self.sender = self.sock.recvfrom(MAX_FRAGMENT + HEADER_SIZE)           # Receive a message and the sender's address

                # Check various flags in the received message
                _, init_request = flag_check(message, ["INIT"], ["FIN", "DATA", "ACK"])
                _, keep_request = flag_check(message, ["KEEP"])
                _, data_init_request = flag_check(message, ["DATA", "INIT"], ["FIN", "ACK"])
                seq_data, data_transition_request = flag_check(message, ["DATA"], ["INIT", "FIN", "ACK"])
                _, data_end_request = flag_check(message, ["DATA", "FIN"], ["INIT", "ACK"])
                _, switch_request = flag_check(message, ["INIT", "FIN"])
                _, end_request = flag_check(message, ["FIN"], ["INIT", "DATA", "ACK"])

                # Handle different types of requests received
                if init_request is not None:                               # Acknowledge INIT request and establish connection
                    self.sock.sendto(packet_construct(["INIT", "ACK"]), self.sender)
                    self.connected = True
                    print(f"Server: Connection with client was successfully established! {self.sender[0]}:{self.sender[1]}")

                elif keep_request is not None:                             # Handle KEEP-ALIVE request
                    if self.connected is False:                            # If not connected, set the connection status to True - handling reconnection
                        self.connected = True
                        print(f"Server: Connection with client was successfully reestablished! {self.sender[0]}:{self.sender[1]}")

                    self.sock.sendto(packet_construct(["KEEP", "ACK"]), self.sender)    # Respond to keep-alive request
                    print(f"Server: Client is alive! ")

                elif data_init_request is not None:                                                 # Process INIT request for data transmission
                    string = str(data_init_request, encoding="utf-8")
                    file_name, size = string.split(",")
                    size = int(size)

                    self.sock.sendto(packet_construct(["DATA", "INIT", "ACK"]), self.sender)        # Acknowledge INIT for data transmission

                elif data_transition_request is not None:                                           # Process DATA transition request (receiving fragments)
                    if start_time == 0:
                        start_time = time.time()

                    _, _, rec_crc = extract_bits_from_header(message[0:5])
                    if rec_crc == binascii.crc_hqx(data_transition_request, 0):               # If CRC matches, acknowledge receipt of data fragment
                        self.sock.sendto(packet_construct(["DATA", "ACK"], sequence_number=seq_data), self.sender)

                        if file_name == '':
                            data_transition_request = str(data_transition_request, encoding='utf-8')

                        # Print received data fragment information
                        print(f"Server: {'Text' if file_name == '' else 'File'} fragment {seq_data + 1} was received successfully: {data_transition_request}")

                        data.append(data_transition_request)                                        # Store received data and fragment position
                        fragment_position.append(seq_data + 1)
                        success += 1
                    else:                                                                           # If CRC doesn't match, send an error acknowledgment
                        self.sock.sendto(packet_construct(["DATA", "ACK", "ERROR"], sequence_number=seq_data), self.sender)
                        fail += 1

                elif data_end_request is not None:                                                  # Process END request for data transmission
                    self.sock.sendto(packet_construct(["DATA", "FIN", "ACK"]), self.sender)

                    pair = sorted(list(zip(fragment_position, data)), key=lambda x: x[0])           # Process END request for data transmission
                    _, num = zip(*pair)
                    stop_time = time.time()

                    if file_name == "":                         # If no filename is provided, create a final message from the received data
                        final_message = "".join(num)
                        print(f"Server: Client sent message: {final_message}")

                    else:                                       # If filename is provided, write the received data to a file
                        index = 1
                        while os.path.exists(file_name):
                            if index == 1:
                                file_name = file_name.replace(".", f"({index}).", 1)
                            else:
                                file_name = file_name.replace(f"({index-1}).", f"({index}).", 1)
                            index += 1

                        with open(file_name, 'wb') as file:
                            file.writelines(num)

                        print(f"Server: Client sent file: {file_name}")

                    transmission_time = stop_time - start_time              # If filename is provided, write the received data to a file

                    print(f"Server: Total fragments: {success} Fragments retransmitted: {fail}")

                    try:
                        speed, ending = rounder(size / transmission_time)
                        print(f"Server: Time of transmission: {round(transmission_time,5)} s Speed of transmission: {speed} {ending}/s")
                    except ZeroDivisionError:
                        continue
                    finally:                                                # Reset variables for next transmission
                        data = []
                        fragment_position = []
                        start_time = 0
                        success = 0
                        fail = 0

                elif switch_request is not None:                            # Handle request to switch connection
                    self.sock.sendto(packet_construct(["INIT", "FIN", "ACK"]), self.sender)
                    print(f"Server: Switching with client! ")
                    self.sock.close()
                    return tuple((self.sender[0], self.port))

                elif end_request is not None:                               # Handle END connection request
                    self.sock.sendto(packet_construct(["FIN", "ACK"]), self.sender)
                    print(f"Server: Client disconnected from server")
                    self.sender = None

            except TimeoutError:                                            # Handling exceptions for timeout during server connection
                self.sock.close()
                print("Server: Server connection timed out")
                return None
