def has_voted(bitfield, index):
    return bool(bitfield[index // 8] & (128 >> (index % 8)))


def set_voted(bitfield, index):
    byte_index = index // 8
    bit_index = index % 8
    new_byte_value = bitfield[byte_index] | (128 >> bit_index)
    return bitfield[:byte_index] + bytes([new_byte_value]) + bitfield[byte_index + 1:]


def get_bitfield_length(attester_count):
    """Return the length of the bitfield for a given number of attesters in bytes."""
    return (attester_count + 7) // 8
