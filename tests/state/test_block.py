from beacon_chain.state.block import (
    Block,
)
from beacon_chain.state.aggregate_vote import (
    AggregateVote,
)
from beacon_chain.utils.bls import (
    privtopub,
)


def test_block_signing():
    block = Block()
    privkey = 1
    pubkey = privtopub(privkey)

    assert not block.verify(pubkey)

    block.sign(1)
    assert block.sig != [0, 0]
    assert block.verify(privtopub(1))

    block.sign(2)
    assert not block.verify(privtopub(1))
    assert block.verify(privtopub(2))

    block.skip_count = 1
    assert not block.verify(privtopub(2))


def test_block_hash():
    block = Block()
    original_block_hash = block.hash

    assert original_block_hash != b'\x00' * 32
    assert len(original_block_hash) == 32

    block.sign(1)
    signed_block_hash_1 = block.hash
    assert signed_block_hash_1 != original_block_hash
    block.sign(2)
    signed_block_hash_2 = block.hash
    assert signed_block_hash_2 != original_block_hash
    assert signed_block_hash_2 != signed_block_hash_1

    block = Block(skip_count=1)
    assert block.hash != original_block_hash
    assert block.hash != signed_block_hash_1
    assert block.hash != signed_block_hash_2


def test_num_properties():
    aggregate_vote = AggregateVote()
    block = Block(
        shard_aggregate_votes=[aggregate_vote],
    )

    assert block.num_shard_aggregate_votes == 1
