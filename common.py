import struct
import binascii
import math

FLAGS = {"FIN": 32, "KEEP": 16, "DATA": 8, "ERROR": 4, "ACK": 2, "INIT": 1}         # Dictionary to map flag names to their respective bit values
MAX_FRAGMENT = 1467                                                                 # Maximum fragment size
HEADER_SIZE = 5                                                                     # Size of the header in bytes


def flag_creation(*args):                                                           # Function to create a combined flag value from a list of flags
    flag_sum = 0x00
    for i in args:
        flag_sum |= FLAGS[i]
    return flag_sum


def packet_construct(flag, sequence_number=0, data=b"", error=False):               # Function to construct a packet with header containing flag, sequence number, and optional data
    flags = flag_creation(*flag)                                                    # Get the combined flag value
    if error:
        header = struct.pack("!BHH", flags, sequence_number, binascii.crc_hqx(data + b'pks :(', 0))
    else:
        header = struct.pack("!BHH", flags, sequence_number, binascii.crc_hqx(data, 0))
    return header + data


def flag_check(message, flag, nflag=()):                                            # Function to decode the flags from the received message and check against expected flags
    def flag_decode(list_flags):
        list_of_flags = []

        for flag_name, flag_value in FLAGS.items():                                 # Decode flags based on their bit values
            if list_flags & flag_value:
                list_of_flags.append(flag_name)

        return list_of_flags

    flag_code, seq, rec_crc = struct.unpack("!BHH", message[0:5])           # Unpack received header
    flags = flag_decode(int(flag_code))

    # Check if all expected positive flags are present and negative flags are absent in the received flags
    if all(pos_flag in flags for pos_flag in flag) and all(neg_flag not in flags for neg_flag in nflag):
        return seq, message[5:]                                                     # Return sequence number and data from the message
    else:
        return None, None                                                           # Return None if flags do not match


def fragment_size_check(size):                                                      # Function to check the size of each fragment for data transmission
    while True:
        fragment_size = int(input("Client: Max fragment size: "))
        if fragment_size < 1:
            print(f"Client: Min fragment size exceeded 1")
            continue

        if fragment_size > MAX_FRAGMENT:
            print(f"Client: Max fragment size exceeded {MAX_FRAGMENT}")
            continue

        if math.ceil(size / fragment_size) > 2 ** 16:                               # Check if the number of fragments required does not exceed the maximum allowed fragments
            print(f"Max fragment count exceeded {2**16}")
            continue

        return fragment_size


def mistake_rate_check():                                                           # Function to check the mistake rate (percentage of simulated mistake packets)
    while True:
        try:
            mistake_rate = float(input("Client: Percentage of mistake packet simulation: ")) / 100
        except ValueError:
            print(f"Client: Insert integer value")                                  # Handle non-integer input
            continue

        if 0 <= mistake_rate <= 1:                                                  # Ensure the mistake rate is between 0 and 1
            return mistake_rate
        else:
            print(f"Client: Mistake rate needs to be in range 0-100")               # Inform the user about the valid range
