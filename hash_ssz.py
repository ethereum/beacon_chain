from hashlib import blake2s
from beacon_chain.state import crystallized_state as cs


def hash(x):
    return blake2s(x).digest()[:32]


CHUNKSIZE = 128


def next_power_of_2(x):
    return x if x == 1 else next_power_of_2((x+1) // 2) * 2


def extend_to_power_of_2(bytez):
    return bytez + b'\x00' * (next_power_of_2(len(bytez)) - len(bytez))


# Concatenate a list of homogeneous objects into data and pad it
def list_to_glob(lst):
    if len(lst) == 0:
        return b''
    if len(lst[0]) != next_power_of_2(len(lst[0])):
        lst = [extend_to_power_of_2(x) for x in lst]
    data = b''.join(lst)
    # Pad to chunksize
    data += b'\x00' * (CHUNKSIZE - (len(data) % CHUNKSIZE or CHUNKSIZE))
    return data


def merkle_hash(lst):
    # Turn list into padded data
    data = list_to_glob(lst)
    # Store length of list (to compensate for non-bijectiveness of padding)
    datalen = len(lst).to_bytes(32, 'big')
    # Convert to chunks
    chunkz = [data[i:i+CHUNKSIZE] for i in range(0, len(data), CHUNKSIZE)]
    # Tree-hash
    while len(chunkz) > 1:
        if len(chunkz) % 2 == 1:
            chunkz.append(b'\x00' * CHUNKSIZE)
        chunkz = [hash(chunkz[i] + chunkz[i+1]) for i in range(0, len(chunkz), 2)]
    # Return hash of root and length data
    return hash((chunkz[0] if len(chunkz) > 0 else b'\x00' * 32) + datalen)


def hash_ssz(val, typ=None):
    if typ is None and hasattr(val, 'fields'):
        typ = type(val)
    if typ in ('hash32', 'address'):
        assert len(val) == 20 if typ == 'address' else 32
        return val
    elif isinstance(typ, str) and typ[:3] == 'int':
        length = int(typ[3:])
        assert length % 8 == 0
        return val.to_bytes(length // 8, 'big', signed=True)
    elif isinstance(typ, str) and typ[:4] == 'uint':
        length = int(typ[4:])
        assert length % 8 == 0
        assert val >= 0
        return val.to_bytes(length // 8, 'big')
    elif typ == 'bytes':
        return hash(val)
    elif isinstance(typ, list):
        assert len(typ) == 1
        return merkle_hash([hash_ssz(x, typ[0]) for x in val])
    elif isinstance(typ, type):
        # NOTE: it's for test
        if typ == cs.ValidatorRecord:
            return hash_validator_record(val)
        elif typ == cs.ShardAndCommittee:
            return hash_shard_and_committee(val)
        else:
            sub = b''.join(
                [hash_ssz(getattr(val, k), typ.fields[k]) for k in sorted(typ.fields.keys())]
            )
            return hash(sub)
    raise Exception("Cannot serialize", val, typ)


def hash_validator_record(val):
    return hash(
        val.pubkey.to_bytes(32, 'big') + val.withdrawal_shard.to_bytes(2, 'big') +
        val.withdrawal_address + val.randao_commitment + val.balance.to_bytes(16, 'big') +
        val.start_dynasty.to_bytes(8, 'big') + val.end_dynasty.to_bytes(8, 'big')
    )


def hash_shard_and_committee(val):
    committee = merkle_hash([x.to_bytes(3, 'big') for x in val.committee])
    return hash(val.shard_id.to_bytes(2, 'big') + committee)
