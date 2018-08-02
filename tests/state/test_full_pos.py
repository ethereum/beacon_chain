import time
import pytest

from beacon_chain.state.new_state_transition import (
    compute_state_transition,
)
from beacon_chain.utils.simpleserialize import serialize


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,epoch_length,'
        'end_epoch_grace_period,min_committee_size,shard_count'
    ),
    [
        (1000, 1000, 20, 4, 10, 100),
    ],
)
def test_state_transition_integration(genesis_crystallized_state,
                                      genesis_active_state,
                                      genesis_block,
                                      mock_make_child,
                                      mock_make_attestations,
                                      config):
    c = genesis_crystallized_state
    a = genesis_active_state
    block = genesis_block
    print('Generated genesis state')
    print('Crystallized state length:', len(serialize(genesis_crystallized_state)))
    print('Active state length:', len(serialize(genesis_active_state)))
    print('Block size:', len(serialize(genesis_block)))

    attestations_of_genesis = mock_make_attestations(
        (c, a),
        block,
        attester_share=0.8
    )

    block2, c2, a2 = mock_make_child((c, a), block, 1, attestations_of_genesis)
    assert block2.slot_number == 1
    assert len(block2.attestations) == len(attestations_of_genesis)
    assert block2.crystallized_state_root == block.crystallized_state_root
    assert block2.active_state_root != b'\x00'*32

    attestations_of_2 = mock_make_attestations(
        (c2, a2),
        block2,
        attester_share=0.8
    )


    # t = time.time()
    # assert compute_state_transition((c, a), block, block2, config=config)
    # print("Normal block (basic attestation only) processed in %.4f sec" % (time.time() - t))
    # print('Verified a block!')
    # block3, c3, a3 = mock_make_child(
        # (c2, a2),
        # block2,
        # 0,
        # attester_share=0.8,
        # crosslink_shards_and_shares=[(0, 0.75)],
    # )
    # print('Verified a block with a committee!')
    # while a3.height % epoch_length > 0:
        # block3, c3, a3 = mock_make_child(
            # (c3, a3),
            # block3,
            # 0,
            # attester_share=0.8,
            # crosslink_shards_and_shares=[(a3.height, 0.6 + 0.02 * a3.height)],
        # )
        # print('Height: %d' % a3.height)
    # print('FFG bitfield:', bin(int.from_bytes(a3.ffg_voter_bitfield, 'big')))
    # block4, c4, a4 = mock_make_child((c3, a3), block3, 1, attester_share=0.55)
    # t = time.time()
    # assert compute_state_transition((c3, a3), block3, block4, config=config)
    # print("Epoch transition processed in %.4f sec" % (time.time() - t))
