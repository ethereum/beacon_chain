import pytest

from beacon_chain.state.block import (
    Block,
)
from beacon_chain.state.chain import (
    Chain,
)
from beacon_chain.state.constants import (
    ZERO_HASH32,
)


def test_head():
    block = Block()
    chain = Chain(head=block)

    assert chain.head == block


def test_block_by_hash():
    block = Block()
    chain = Chain(head=block, blocks=[block])

    assert chain.get_block_by_hash(block.hash) == block
    assert chain.get_block_by_hash(b'\x35'*32) is None


@pytest.mark.parametrize(
    'slot_number',
    [(1), (10), (1000)]
)
def test_block_by_slot_number(slot_number):
    block = Block(slot_number=slot_number)
    chain = Chain(head=block, blocks=[block])

    assert chain.get_block_by_slot_number(block.slot_number) == block
    assert chain.get_block_by_slot_number(block.slot_number + 1) is None
    assert chain.get_block_by_slot_number(-1) is None


def test_chain():
    block = None
    parent_hash = ZERO_HASH32
    blocks = []
    for slot_number in range(1, 10):
        block = Block(
            slot_number=slot_number,
            parent_hash=parent_hash
        )
        blocks.append(block)
        parent_hash = block.hash

    extra_block = Block(slot_number=1000000)
    chain = Chain(head=block, blocks=blocks + [extra_block])
    assert len(chain.chain) == len(blocks)
    for block in blocks:
        assert block in chain
    assert extra_block not in chain
