import threading
import struct
import binascii

RECEIVER_IP = None
RECEIVER_PORT = None
SENDER_IP = None
SENDER_PORT = None

FLAGS = {"SWITCH": 128, "FIN": 64, "KEEP": 32, "FILE": 16, "TXT": 8, "ERROR": 4, "ACK": 2, "INIT": 1}


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


def info_messages(flag, message=""):
    flags = flag_creation(*flag)
    header = struct.pack("!BHHH", flags, 0, 0, crc_creation(flags))
    return header + bytes(message, encoding="utf-8")


def crc_creation(flags):
    header = struct.pack("!BHH", flags, 0, 0)
    crc = binascii.crc_hqx(header, 0)
    return crc


def flag_check(message, flag, nflag=()):
    flag_code, length, seq, rec_crc = struct.unpack("!BHHH", message[0:7])
    flags = flag_decode(int(flag_code))
    flags_number = flag_creation(*flags)

    if crc_creation(flags_number) == rec_crc and all(pos_flag in flags for pos_flag in flag) and all(neg_flag not in flags for neg_flag in nflag):
        return str(message[7:], encoding="utf-8")
    else:
        return None
