import time
import pytest

from ssz import (
    serialize,
)

from beacon_chain.state.state_transition import (
    compute_state_transition,
)


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,shard_count'
    ),
    [
        (100, 1000, 50, 10, 10),
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
            len(c.shard_and_committee_for_slots[attestations_of_genesis[0].slot][0].committee),
            (time.time() - t))
        )
    print('Verified a block!')

    attestations_of_2 = mock_make_attestations(
        (c2, a2),
        block2,
        attester_share=0.8
    )

    cycle_transition_slot = c2.last_state_recalc + config['cycle_length']

    block3, c3, a3 = mock_make_child(
        (c2, a2),
        block2,
        cycle_transition_slot,
        attestations_of_2
    )

    t = time.time()
    assert compute_state_transition((c2, a2), block2, block3, config=config)
    print("Cycle transition processed in %.4f sec" % (time.time() - t))


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,min_dynasty_length,shard_count'
    ),
    [
        # all of these combinations allow for full committees for
        # all shards within one cycle
        (100, 100, 10, 5, 20, 2),
        (100, 1000, 50, 10, 50, 10),
        (1000, 1000, 20, 10, 80, 10),
    ],
)
def test_pos_finalization(genesis_crystallized_state,
                          genesis_active_state,
                          genesis_block,
                          mock_make_child,
                          mock_make_attestations,
                          config):
    c = genesis_crystallized_state
    a = genesis_active_state
    block = genesis_block
    expected_streak = 0
    assert c.justified_streak == expected_streak

    # create 100% full vote blocks to one block before cycle transition
    for i in range(config['cycle_length'] - 1):
        attestations = mock_make_attestations(
            (c, a),
            block,
            attester_share=1.0
        )
        block, c, a = mock_make_child((c, a), block, block.slot_number + 1, attestations)

    assert c.last_state_recalc == genesis_crystallized_state.last_state_recalc
    assert c.justified_streak == 0

    # do cycle transition
    attestations = mock_make_attestations(
        (c, a),
        block,
        attester_share=1.0
    )
    block, c, a = mock_make_child((c, a), block, block.slot_number + 1, attestations)

    assert c.last_state_recalc == (
        genesis_crystallized_state.last_state_recalc +
        config['cycle_length']
    )
    assert c.justified_streak == config['cycle_length']
    assert c.last_justified_slot == 0
    assert c.last_finalized_slot == 0

    # check that the expected crosslinks were updated
    expected_shards = [
        shard_and_committee.shard_id
        for indices in c.shard_and_committee_for_slots
        for shard_and_committee in indices
    ]
    for shard_id, crosslink in enumerate(c.crosslink_records):
        if shard_id in expected_shards:
            assert crosslink.slot == c.last_state_recalc
        else:
            assert crosslink.slot == 0

    # create 100% full vote blocks to one block before cycle transition
    for i in range(config['cycle_length'] - 1):
        attestations = mock_make_attestations(
            (c, a),
            block,
            attester_share=1.0
        )
        block, c, a = mock_make_child((c, a), block, block.slot_number + 1, attestations)

        # Nothing occurs because we haven't triggered cycle transition
        assert c.last_state_recalc == (
            genesis_crystallized_state.last_state_recalc +
            config['cycle_length']
        )
        assert c.justified_streak == config['cycle_length']
        assert c.last_justified_slot == 0
        assert c.last_finalized_slot == 0

    # do cycle transition
    attestations = mock_make_attestations(
        (c, a),
        block,
        attester_share=1.0
    )
    block, c, a = mock_make_child((c, a), block, block.slot_number + 1, attestations)

    assert c.last_state_recalc == (
        genesis_crystallized_state.last_state_recalc +
        config['cycle_length'] * 2
    )
    assert c.justified_streak == config['cycle_length'] * 2
    assert c.last_justified_slot == c.last_state_recalc - config['cycle_length'] - 1
    # still 0 because CYCLE_LENGTH + 1 before lsat_justified_slot is negative
    assert c.last_finalized_slot == 0

    # One more cycle!
    for i in range(config['cycle_length'] - 1):
        attestations = mock_make_attestations(
            (c, a),
            block,
            attester_share=1.0
        )
        block, c, a = mock_make_child((c, a), block, block.slot_number + 1, attestations)

    # do cycle transition
    attestations = mock_make_attestations(
        (c, a),
        block,
        attester_share=1.0
    )
    block, c, a = mock_make_child((c, a), block, block.slot_number + 1, attestations)

    assert c.last_state_recalc == (
            genesis_crystallized_state.last_state_recalc +
            config['cycle_length'] * 3
    )
    assert c.justified_streak == config['cycle_length'] * 3
    assert c.last_justified_slot == c.last_state_recalc - config['cycle_length'] - 1
    # still 0 because CYCLE_LENGTH + 1 before last_justified_slot is negative
    assert c.last_finalized_slot == c.last_justified_slot - config['cycle_length'] - 1

    # force and check dynasty transition
    if block.slot_number < config['min_dynasty_length']:
        block, c, a = mock_make_child((c, a), block, config['min_dynasty_length'], [])

    assert c.current_dynasty == genesis_crystallized_state.current_dynasty + 1
    assert c.dynasty_start == c.last_state_recalc
