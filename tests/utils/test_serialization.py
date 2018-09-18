from ssz import (
    serialize,
    deserialize,
    eq,
)

from beacon_chain.state.active_state import (
    ActiveState,
)
from beacon_chain.state.partial_crosslink_record import (
    PartialCrosslinkRecord,
)


def test_active_state_serialization():
    s = ActiveState()
    ds = deserialize(serialize(s, type(s)), type(s))
    assert eq(s, ds)

    s = ActiveState(
        partial_crosslinks=[
            PartialCrosslinkRecord(
                shard_id=42,
                shard_block_hash=b'\x55'*32,
                voter_bitfield=b'31337dawg'
            )
        ],
        height=555,
        randao=b'\x88'*32,
    )
    ds = deserialize(serialize(s, type(s)), type(s))
    assert eq(s, ds)
