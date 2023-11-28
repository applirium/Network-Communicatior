import math
import random
import socket
import threading
from common import flag_check, packet_construct, fragment_size_check, rounder, mistake_rate_check, MAX_FRAGMENT, MAX_FRAMES
import time
import os


class Sender:
    def __init__(self, switch=None):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                if switch is None:                                                  # If switch is None, prompt for IP and port, else use the provided switch values
                    self.ip = input("Sender IP: ")                                  # Get the sender's IP address
                    self.port = int(input("Sender port: "))                         # Get the sender's port number
                else:
                    self.ip = switch[0]                                             # Use the provided IP and port from the switch
                    self.port = switch[1]

                self.sock.sendto(packet_construct(["INIT"]), (self.ip, self.port))  # Send an INIT packet to establish connection with the receiver

                self.sock.settimeout(5)                                             # Set a timeout for receiving a response from the receiver
                message, self.receiver = self.sock.recvfrom(MAX_FRAGMENT)

                _, init_command = flag_check(message, ["INIT", "ACK"], ["DATA"])        # Check the received message for INIT/ACK flags and absence of DATA flag

                if init_command is not None:
                    print(f"Client: Connection successfully established with server! {self.receiver[0]}:{self.receiver[1]}")

                self.thread_status = True                                           # Set thread status to True and start a thread for keep-alive mechanism

                self.thread = threading.Thread(target=self.keep_alive)
                self.thread.daemon = True
                self.thread.start()
                break

            except (ConnectionResetError, TimeoutError):
                print(f"Client: Server is not responding")

    def request(self):
        while True:
            action = input("Client: Actions Client: Disconnect | Switch | Text | File: ").lower()

            if action == "disconnect":                                              # Disconnecting client from server
                self.sock.sendto(packet_construct(["FIN"]), self.receiver)          # Send FIN packet to signal disconnection to the receiver
                data = self.sock.recv(MAX_FRAGMENT)

                _, end_command = flag_check(data, ["FIN", "ACK"])

                if end_command is not None:
                    self.thread_status = False
                    self.thread.join()                                              # Set thread status to False, wait for the thread to join, close the socket, and print disconnection message
                    self.sock.close()

                    print(f"Client: Disconnected from server")
                    return None

            elif action == "file" or action == "text":                              # Sending file or text
                buffed_file = b""                                                   # Initialize variable for file content
                message = ""                                                        # Initialize variable for text message
                buffer_sent = []                                                    # Initialize buffer for sent fragments
                message_split = []                                                  # Initialize list to hold split message fragments
                file_split = []                                                     # Initialize list to hold split file fragments
                packet_transfer = 0                                                 # Initialize packet transfer count

                if action == "file":                                                # Handle sending file
                    while True:
                        try:
                            fragment_size = fragment_size_check()                   # Determine fragment size for the text
                            max_file_size, ending = rounder(fragment_size * MAX_FRAMES)
                            print(f"Client: Max file size = {max_file_size} {ending}")

                            path = input("Client: Set name of a file : ")
                            absolute_path = os.path.abspath(path)
                            size = os.path.getsize(path)

                            current_file_size, current_ending = rounder(size)
                            if size > fragment_size * MAX_FRAMES:                        # Check file size limit
                                print(f"Client: File size {current_file_size} {current_ending} is over the maximum file size limit: {max_file_size} {ending}")
                                continue

                            file = open(absolute_path, "rb")                        # Read file content into buffed_file
                            buffed_file = file.read()
                            file.close()

                            packet_transfer = math.ceil(size / fragment_size)                            # Calculate total packets to send
                            print(f"Client: File: {path} Size: {current_file_size} {current_ending}")    # Display file details
                            print(f"Client: Absolute path: {absolute_path}")
                            print(f"Client: Sending {packet_transfer} packets!")
                            break

                        except FileNotFoundError:
                            print("Client: File not found")

                else:                                                                  # Handle sending text
                    while True:
                        fragment_size = fragment_size_check()                          # Determine fragment size for the text
                        max_text_size, ending = rounder(fragment_size * MAX_FRAMES)
                        print(f"Client: Max message size = {max_text_size} {ending}")

                        path = ""
                        message = input("Client: Input message to send: ")              # Get text input from user
                        size = len(message)

                        current_text_size, current_ending = rounder(size)
                        if size > fragment_size * MAX_FRAMES:                                # Check file size limit
                            print(f"Client: File size {current_text_size} {current_ending} is over the maximum file size limit: {max_text_size} {ending}")
                            continue

                        packet_transfer = math.ceil(size / fragment_size)               # Calculate total packets to send
                        print(f"Client: Message: {message}")
                        print(f"Client: Size: {current_text_size} {current_ending}")
                        print(f"Client: Sending {packet_transfer} packets!")
                        break

                window_size = min(4, packet_transfer)                               # Set window size for sending fragments
                buffer = list(range(packet_transfer))                               # Initialize buffer for unsent fragments
                mistake_rate = mistake_rate_check()                                 # Determine mistake rate for packet simulation

                # Send INIT packet with file/text details to the receiver
                self.sock.sendto(packet_construct(["DATA", "INIT"], data=bytes(f"{path},{size}", encoding="utf-8")), self.receiver)
                data = self.sock.recv(MAX_FRAGMENT)

                # Checks for acknowledgment of the INIT packet
                _, data_init_command = flag_check(data, ["DATA", "INIT", "ACK"])

                if data_init_command is not None:
                    self.thread_status = False
                    self.thread.join()

                    if path == "":                                                  # Split file/text into fragments based on the determined fragment size
                        message_split = [message[i:i + fragment_size] for i in range(0, len(message), fragment_size)]
                    else:
                        file_split = [buffed_file[i:i + fragment_size] for i in range(0, len(buffed_file), fragment_size)]

                while len(buffer) > 0 or len(buffer_sent) > 0:                       # Start sending fragments while buffer or buffer_sent is not empty
                    while len(buffer_sent) < window_size and len(buffer) > 0:        # Fill buffer_sent with fragments to be sent based on window size
                        error_flag = random.random() < mistake_rate                  # Simulate errors based on mistake rate

                        # Prepare data to be sent (text or file fragment)
                        if path == "":
                            data_to_send = bytes(message_split[buffer[0]], encoding='utf-8')
                        else:
                            data_to_send = file_split[buffer[0]]

                        # Create packet to send with the appropriate sequence number and error flag
                        packet_to_send = packet_construct(["DATA"], sequence_number=buffer[0], data=data_to_send, error=error_flag)

                        self.sock.sendto(packet_to_send, self.receiver)             # Send the packet to the receiver and move the fragment from buffer to buffer_sent
                        buffer_sent.append(buffer.pop(0))

                    try:
                        data = self.sock.recv(MAX_FRAGMENT)
                    except TimeoutError:                                            # Handling not receiving an acknowledgment from server
                        buffer.insert(0, buffer_sent.pop())
                        continue

                    # Check received data for acknowledgments or errors for sent fragments
                    seq_res, data_transfer_command = flag_check(data, ["DATA", "ACK"], ["INIT", "FIN", "ERROR"])
                    seq_err, data_transfer_error = flag_check(data, ["DATA", "ACK", "ERROR"], ["INIT", "FIN"])

                    reminder = size % fragment_size
                    if reminder == 0:
                        reminder = fragment_size

                    if data_transfer_command is not None:                            # Print success message for successfully sent fragments
                        buffer_sent.remove(seq_res)

                        print(f"Client: {'Text' if path == '' else 'File'} fragment {seq_res + 1} size: {reminder if seq_res + 1 == packet_transfer else fragment_size} B was sent successfully!")

                    if data_transfer_error is not None:                              # Handle error message for fractured fragments
                        seq_to_remove = buffer_sent.index(seq_err)
                        buffer.insert(0, buffer_sent.pop(seq_to_remove))

                        print(f"Client: {'Text' if path == '' else 'File'} fragment {seq_err + 1} size: {reminder if seq_err + 1 == packet_transfer else fragment_size} B was fractured!")

                self.sock.sendto(packet_construct(["DATA", "FIN"]), self.receiver)   # Send FIN packet to signal end of data transmission
                data = self.sock.recv(MAX_FRAGMENT)

                _, data_end_command = flag_check(data, ["DATA", "FIN", "ACK"])  # Checks for acknowledgment of the FIN packet

                # If acknowledgment received, restarting a new thread for client keep alive mechanism
                if data_end_command is not None:
                    self.thread_status = True

                    self.thread = threading.Thread(target=self.keep_alive)
                    self.thread.daemon = True
                    self.thread.start()

            elif action == "switch":                                                # Handling action 'switch' to change the connection to another server
                self.sock.sendto(packet_construct(["INIT", "FIN"]), self.receiver)
                data = self.sock.recv(1024)

                _, end_command = flag_check(data, ["INIT", "FIN", "ACK"])

                if end_command is not None:
                    self.thread_status = False
                    self.thread.join()
                    self.sock.close()

                    print(f"Client: Switching with server!")
                    return self.port

            elif action == "end":                                                   # Handling action 'end' to terminate the program
                return None

            else:
                print("Client: Invalid input")

    def keep_alive(self):                                                           # Method for the keep alive mechanism
        not_responding = 0
        self.sock.settimeout(5)

        while self.thread_status:                                                   # While the thread status is True (indicating the thread is active)
            try:
                self.sock.sendto(packet_construct(["KEEP"]), self.receiver)         # Send a KEEP packet to check server response
                data = self.sock.recv(MAX_FRAGMENT)

                _, keep_request = flag_check(data, ["KEEP", "ACK"])            # Check for the acknowledgment of the KEEP packet

                if keep_request is not None:                                        # If an acknowledgment is received
                    not_responding = 0                                              # Reset the not_responding counter to 0
                    time.sleep(5)                                                   # Wait for 5 seconds before sending the next KEEP packet

            except (TimeoutError, ConnectionResetError):                            # Handle timeout or connection reset errors
                not_responding += 1
                if not_responding < 4:                                              # If the server hasn't responded for less than 4 consecutive times
                    print(f"Client: Server is not responding! ")                    # Print a message indicating server unresponsiveness
                    time.sleep(5)
                else:                                                               # If the server hasn't responded for 4 consecutive times, return a connection interruption
                    print(f"Client: Connection was interrupted, press end to terminate program! ")
                    return None
