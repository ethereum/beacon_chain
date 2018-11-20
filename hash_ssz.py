from hashlib import blake2s
from beacon_chain.state import crystallized_state as cs


def hash(x):
    return blake2s(x).digest()[:32]


CHUNKSIZE = 128


# Merkle tree hash of a list of homogenous, non-empty items
def merkle_hash(lst):
    # Store length of list (to compensate for non-bijectiveness of padding)
    datalen = len(lst).to_bytes(32, 'big')

    if len(lst) == 0:
        # Handle empty list case
        chunkz = [b'\x00' * CHUNKSIZE]
    elif len(lst[0]) < CHUNKSIZE:
        # See how many items fit in a chunk
        items_per_chunk = CHUNKSIZE // len(lst[0])

        # Build a list of chunks based on the number of items in the chunk
        chunkz = [b''.join(lst[i:i+items_per_chunk]) for i in range(0, len(lst), items_per_chunk)]
    else:
        # Leave large items alone
        chunkz = lst

    # Tree-hash
    while len(chunkz) > 1:
        if len(chunkz) % 2 == 1:
            chunkz.append(b'\x00' * CHUNKSIZE)
        chunkz = [hash(chunkz[i] + chunkz[i+1]) for i in range(0, len(chunkz), 2)]

    # Return hash of root and length data
    return hash(chunkz[0] + datalen)


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
