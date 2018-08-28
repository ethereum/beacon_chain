from beacon_chain.utils.blake import blake
from beacon_chain.utils.simpleserialize import (
    serialize,
)


KEY_CANONICAL_HEAD_HASH = blake(b'CANONICAL_HEAD_HASH')
KEY_CANONICAL_HEAD_SCORE = blake(b'CANONICAL_HEAD_SCORE')


class BeaconChainDB:
    db = None

    def __init__(self, db):
        self.db = db

    def persist_block(self, block):
        block_hash = blake(serialize(block))
        self.db.set(
            block_hash,
            block,
        )

        # TODO: Apply fork choice rule here
        is_head = True
        score = block.slot_number

        if is_head:
            self.db.set(
                KEY_CANONICAL_HEAD_SCORE,
                score,
            )
            self.db.set(
                KEY_CANONICAL_HEAD_HASH,
                block_hash
            )

    def get_canonical_block_head(self):
        canonical_block_head = None
        if self.db.exists(KEY_CANONICAL_HEAD_HASH):
            canonical_block_hash = self.db[KEY_CANONICAL_HEAD_HASH]
            canonical_block_head = self.db[canonical_block_hash]

        return canonical_block_head
