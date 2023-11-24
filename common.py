import struct
import binascii
import math

FLAGS = {"FIN": 32, "KEEP": 16, "DATA": 8, "ERROR": 4, "ACK": 2, "INIT": 1}
MAX_FRAGMENT = 1467


def flag_creation(*args):
    flag_sum = 0x00
    for i in args:
        flag_sum |= FLAGS[i]
    return flag_sum


def packet_construct(flag, sequence_number=0, data=b"", error=False):
    flags = flag_creation(*flag)
    if error:
        header = struct.pack("!BHH", flags, sequence_number, binascii.crc_hqx(data + b'xD', 0))
    else:
        header = struct.pack("!BHH", flags, sequence_number, binascii.crc_hqx(data, 0))
    return header + data


def flag_check(message, flag, nflag=()):
    def flag_decode(list_flags):
        list_of_flags = []

        for flag_name, flag_value in FLAGS.items():
            if list_flags & flag_value:
                list_of_flags.append(flag_name)

        return list_of_flags

    flag_code, seq, rec_crc = struct.unpack("!BHH", message[0:5])
    flags = flag_decode(int(flag_code))

    if all(pos_flag in flags for pos_flag in flag) and all(neg_flag not in flags for neg_flag in nflag):
        return seq, str(message[5:], encoding="utf-8")
    else:
        return None, None


def fragment_size_check(size):
    while True:
        fragment_size = int(input("Client: Max fragment size: "))
        if 1 <= fragment_size <= MAX_FRAGMENT and math.ceil(size / fragment_size) <= 2 ** 16:
            return fragment_size
        else:
            print(f"Client: Max fragment size exceeded {MAX_FRAGMENT} or Max fragment count exceeded {2**16}")


def mistake_rate_check():
    while True:
        mistake_rate = float(input("Client: Percentage of mistake packet simulation: ")) / 100
        if 0 <= mistake_rate <= 1:
            return mistake_rate
        else:
            print(f"Client: Mistake rate needs to be in range 0-100")