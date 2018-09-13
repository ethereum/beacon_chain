from beacon_chain.db.chain import (
    BeaconChainDB,
)


class BeaconChain:
    def __init__(self, base_db):
        self.chaindb = BeaconChainDB(base_db)

    def import_block(self, block):
        # TODO validation
        self.chaindb.persist_block(block)

    def get_block_by_hash(self, block_hash):
        pass

    def get_canonical_block_head(self):
        return self.chaindb.get_canonical_block_head()

    def get_canonical_block_by_slot(self, slot):
        pass
