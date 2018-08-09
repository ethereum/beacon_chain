import time
import pytest

from beacon_chain.state.state_transition import (
    compute_state_transition,
)
from beacon_chain.utils.simpleserialize import serialize


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,epoch_length,'
        'min_committee_size,shard_count'
    ),
    [
        (1000, 1000, 20, 10, 100),
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

    t = time.time()
    assert compute_state_transition((c, a), block, block2, config=config)
    print(
        "Normal block with %s attestations of size %s processed in %.4f sec" %
        (
            len(attestations_of_genesis),
            len(c.indices_for_heights[attestations_of_genesis[0].slot][0].committee),
            (time.time() - t))
        )
    print('Verified a block!')

    attestations_of_2 = mock_make_attestations(
        (c2, a2),
        block2,
        attester_share=0.8
    )

    epoch_transition_slot = (c2.epoch_number + 1) * config['epoch_length']

    block3, c3, a3 = mock_make_child(
        (c2, a2),
        block2,
        epoch_transition_slot,
        attestations_of_2
    )

    t = time.time()
    assert compute_state_transition((c2, a2), block2, block3, config=config)
    print("Epoch transition processed in %.4f sec" % (time.time() - t))
