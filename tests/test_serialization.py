import pytest

from beacon_chain.full_pos import (
    ActiveState,
    CheckpointRecord,
)
from beacon_chain.simpleserialize import (
    serialize,
    deserialize,
    eq,
)


@pytest.mark.parametrize(
    'value, typ, data',
    [
        (5, 'int8', b'\x05'),
        (2**32-3, 'int40', b'\x00\xff\xff\xff\xfd'),
        (b'\x35'*20, 'address', b'\x35'*20),
        (b'\x35'*32, 'hash32', b'\x35'*32),
        (b'cow', 'bytes', b'\x00\x00\x00\x03cow'),
    ]
)
def test_basic_serialization(value, typ, data):
    assert serialize(value, typ) == data
    assert deserialize(data, typ) == value


def test_active_state_serialization():
    s = ActiveState()
    ds = deserialize(serialize(s, type(s)), type(s))
    assert eq(s, ds)

    s = ActiveState(
        checkpoints=[
            CheckpointRecord(shard_id=42, checkpoint_hash=b'\x55'*32, voter_bitmask=b'31337dawg')
        ],
        height=555,
        randao=b'\x88'*32,
        balance_deltas=[5, 7, 9, 579] + [3] * 333
    )
    ds = deserialize(serialize(s, type(s)), type(s))
    assert eq(s, ds)
