import pytest

from beacon_chain.state.attestation_record import (
    AttestationRecord,
)
from beacon_chain.state.block import (
    Block,
)


def test_block_hash():
    block = Block()
    original_block_hash = block.hash

    assert original_block_hash != b'\x00' * 32
    assert len(original_block_hash) == 32

    block = Block(slot_number=1)
    assert block.hash != original_block_hash


@pytest.mark.parametrize(
    'expected', [(0), (1), (5)]
)
def test_num_attestations(expected):
    attestations = [AttestationRecord() for i in range(expected)]
    block = Block(
        attestations=attestations,
    )

    assert block.num_attestations == expected
