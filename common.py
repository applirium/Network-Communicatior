import binascii

FLAGS = {"FIN": 32, "KEEP": 16, "DATA": 8, "ERROR": 4, "ACK": 2, "INIT": 1}         # Dictionary to map flag names to their respective bit values
MAX_FRAGMENT = 1467                                                                 # Maximum fragment size
MAX_FRAMES = 2**18
HEADER_SIZE = 5                                                                     # Size of the header in bytes


def flag_creation(*args):                                                           # Function to create a combined flag value from a list of flags
    flag_sum = 0x00
    for i in args:
        flag_sum |= FLAGS[i]
    return flag_sum


def create_header(bit_6, bit_18, bit_16):                                           # Function to create the 5 byte header for the packet
    header = (bit_6 & 0b111111) << 34
    header |= (bit_18 & 0b111111111111111111) << 16
    header |= bit_16 & 0b1111111111111111
    return header.to_bytes(5)


def extract_bits_from_header(header):                                               # Function to extract bits from my custom header
    header = int.from_bytes(header)

    bit_6 = (header >> 34) & 0b111111
    bit_18 = (header >> 16) & 0b111111111111111111
    bit_16 = header & 0b1111111111111111
    return bit_6, bit_18, bit_16


def packet_construct(flag, sequence_number=0, data=b"", error=False):               # Function to construct a packet with header containing flag, sequence number, and optional data
    flags = flag_creation(*flag)                                                    # Get the combined flag value
    if error:
        header = create_header(flags, sequence_number, binascii.crc_hqx(data + b'pks :(', 0))
    else:
        header = create_header(flags, sequence_number, binascii.crc_hqx(data, 0))

    return header + data


def flag_check(message, flag, not_flag=()):                                            # Function to decode the flags from the received message and check against expected flags
    def flag_decode(list_flags):
        list_of_flags = []

        for flag_name, flag_value in FLAGS.items():                                     # Decode flags based on their bit values
            if list_flags & flag_value:
                list_of_flags.append(flag_name)

        return list_of_flags

    flag_code, seq, rec_crc = extract_bits_from_header(message[0:5])                # Unpack received header
    flags = flag_decode(int(flag_code))

    # Check if all expected positive flags are present and negative flags are absent in the received flags
    if all(pos_flag in flags for pos_flag in flag) and all(neg_flag not in flags for neg_flag in not_flag):
        return seq, message[5:]                                                     # Return sequence number and data from the message
    else:
        return None, None                                                           # Return None if flags do not match


def fragment_size_check():  # Function to check the size of each fragment for data transmission
    while True:
        try:
            fragment_size = int(input("Client: Max fragment size: "))
            if fragment_size < 1:
                print(f"Client: Min fragment size is 1")
            elif fragment_size > MAX_FRAGMENT:
                print(f"Client: Max fragment size is {MAX_FRAGMENT}")
            else:
                return fragment_size
        except ValueError:
            print("Client: Insert an integer value")  # Handle non-integer input


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


def rounder(size):                                                                  # Function to round numbers and determine their appropriate suffix (B, KB, MB, GB)
    endings = ["B", "KB", "MB", "GB"]
    index = 0

    while size >= 1024 and index < len(endings)-1:
        size /= 1024
        index += 1

    return round(size, 3), endings[index]
