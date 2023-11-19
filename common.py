import threading
import struct
import binascii

RECEIVER_IP = None
RECEIVER_PORT = None
SENDER_IP = None
SENDER_PORT = None

FLAGS = {"FIN": 64, "KEEP": 32, "FILE": 16, "TXT": 8, "ERROR": 4, "ACK": 2, "INIT": 1}

def flag_creation(*args):
    flag_sum = 0x00
    for i in args:
        flag_sum |= FLAGS[i]
    return flag_sum


def flag_decode(flags):
    list_of_flags = []

    for flag_name, flag_value in FLAGS.items():
        if flags & flag_value:
            list_of_flags.append(flag_name)

    return list_of_flags


def info_messages(flag):
    flags = flag_creation(*flag)
    header = struct.pack("!cHHH", str.encode(str(flags)), 0, 0, crc_creation(flags))
    return header


def crc_creation(flags):
    header = struct.pack("!cHH", str.encode(str(flags)), 0, 0)
    crc = binascii.crc_hqx(header, 0)
    return crc


def flag_check(message, flag):
    flag_code, length, seq, rec_crc = struct.unpack("!cHHH", message)
    flags = flag_decode(int(flag_code))
    flags_number = flag_creation(*flags)

    if crc_creation(flags_number) == rec_crc and flag in flags:
        return True
    else:
        return False
