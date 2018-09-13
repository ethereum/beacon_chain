from eth.db.backends.memory import MemoryDB

from beacon_chain.chains.chain import (
    BeaconChain
)


def test_simple_chain(genesis_block):
    db = MemoryDB()
    chain = BeaconChain(db)
    chain.import_block(genesis_block)
    assert chain.get_canonical_block_head() == genesis_block
