import pytest

from beacon_chain.state.attestation_record import (
    AttestationRecord,
)
from beacon_chain.state.block import (
    Block,
)

# from beacon_chain.utils.bls import (
    # privtopub,
# )


# def test_block_signing():
    # block = Block()
    # privkey = 1
    # pubkey = privtopub(privkey)

    # assert not block.verify(pubkey)

    # block.sign(1)
    # assert block.sig != [0, 0]
    # assert block.verify(privtopub(1))

    # block.sign(2)
    # assert not block.verify(privtopub(1))
    # assert block.verify(privtopub(2))

    # block.skip_count = 1
    # assert not block.verify(privtopub(2))


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
