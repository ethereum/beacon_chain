from typing import (
    List,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from .block import Block  # noqa: F401


class Chain():
    # Note, this is not an object defined in the v2.1 spec
    # this is a helper object to mask complexity in tracking
    # blocks

    def __init__(self, head: 'Block'=None, blocks: List['Block']=[]) -> None:
        self.head = head
        self.blocks = blocks
        self.chain = []  # type: List['Block']

        # temp helper
        all_blocks_by_hash = {
            block.hash: block
            for block in self.blocks
        }

        if self.head:
            tmp = self.head
            self.chain.append(tmp)
            while all_blocks_by_hash.get(tmp.parent_hash, None):
                tmp = all_blocks_by_hash[tmp.parent_hash]
                self.chain.append(tmp)

        self.block_by_hash = {
            block.hash: block
            for block in self.chain
        }
        self.block_by_slot_number = {
            block.slot_number: block
            for block in self.chain
        }

    def __contains__(self, block: 'Block') -> bool:
        return bool(self.get_block_by_hash(block.hash))

    def get_block_by_slot_number(self, slot_number: int) -> 'Block':
        return self.block_by_slot_number.get(slot_number, None)

    def get_block_by_hash(self, block_hash: bytes) -> 'Block':
        return self.block_by_hash.get(block_hash, None)
