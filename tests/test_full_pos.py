import time

from beacon_chain.utils import (
    SHARD_COUNT,
    compute_state_transition,
)
from beacon_chain.simpleserialize import serialize


def test_all(genesis_crystallized_state,
             genesis_active_state,
             genesis_block,
             mock_make_child):
    c = genesis_crystallized_state
    a = genesis_active_state
    block = genesis_block
    print('Generated genesis state')
    print('Crystallized state length:', len(serialize(genesis_crystallized_state)))
    print('Active state length:', len(serialize(genesis_active_state)))
    print('Block size:', len(serialize(genesis_block)))

    block2, c2, a2 = mock_make_child((c, a), block, 0, 0.8, [])
    t = time.time()
    assert compute_state_transition((c, a), block, block2)
    print("Normal block (basic attestation only) processed in %.4f sec" % (time.time() - t))
    print('Verified a block!')
    block3, c3, a3 = mock_make_child((c2, a2), block2, 0, 0.8, [(0, 0.75)])
    print('Verified a block with a committee!')
    while a3.height % SHARD_COUNT > 0:
        block3, c3, a3 = mock_make_child((c3, a3), block3, 0, 0.8, [(a3.height, 0.6 + 0.02 * a3.height)])
        print('Height: %d' % a3.height)
    print('FFG bitmask:', bin(int.from_bytes(a3.ffg_voter_bitmask, 'big')))
    block4, c4, a4 = mock_make_child((c3, a3), block3, 1, 0.55, [])
    t = time.time()
    assert compute_state_transition((c3, a3), block3, block4)
    print("Epoch transition processed in %.4f sec" % (time.time() - t))
