def has_voted(bitfield, index):
    return bool(bitfield[index // 8] & (128 >> (index % 8)))


def set_voted(bitfield, index):
    byte_index = index // 8
    bit_index = index % 8
    new_byte_value = bitfield[byte_index] | (128 >> bit_index)
    return bitfield[:byte_index] + bytes([new_byte_value]) + bitfield[byte_index + 1:]


def get_bitfield_length(bit_count):
    """Return the length of the bitfield for a given number of attesters in bytes."""
    return (bit_count + 7) // 8


def get_empty_bitfield(bit_count):
    return b"\x00" * get_bitfield_length(bit_count)


def get_vote_count(bitfield):
    votes = 0
    for index in range(len(bitfield) * 8):
        if has_voted(bitfield, index):
            votes += 1
    return votes


def or_bitfields(bitfields):
    new = b''
    for i in range(len(bitfields[0])):
        byte = 0
        for bitfield in bitfields:
            byte = bitfield[i] | byte
        new += bytes([byte])
    return new
