import copy

import pytest

from eth_utils import (
    ValidationError,
)

from ssz import (
    serialize,
)

from beacon_chain.utils.blake import blake
from beacon_chain.utils.bitfield import (
    get_empty_bitfield,
    has_voted,
    set_voted,
)

from beacon_chain.state.chain import (
    Chain,
)
from beacon_chain.state.helpers import (
    get_attestation_indices,
    get_shards_and_committees_for_slot,
)
from beacon_chain.state.state_transition import (
    fill_recent_block_hashes,
    calculate_crosslink_rewards,
    compute_cycle_transitions,
    initialize_new_cycle,
    validate_attestation,
)


@pytest.fixture
def attestation_validation_fixture(
        genesis_crystallized_state,
        genesis_active_state,
        genesis_block,
        mock_make_child,
        mock_make_attestations,
        config):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block
    active_state.chain = Chain(head=parent_block, blocks=[parent_block])
    attestations_of_genesis = mock_make_attestations(
        (crystallized_state, active_state),
        parent_block,
        attester_share=1.0
    )
    block, _, _ = mock_make_child(
        (crystallized_state, active_state),
        parent_block,
        1,
        attestations_of_genesis,
    )
    attestation = attestations_of_genesis[0]

    return (
        crystallized_state,
        active_state,
        attestation,
        block,
        parent_block,
    )


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,shard_count'
    ),
    [
        (100, 1000, 50, 10, 10),
    ],
)
def test_validate_attestation_valid(attestation_validation_fixture, config):
    (
        crystallized_state,
        active_state,
        attestation,
        block,
        parent_block
    ) = attestation_validation_fixture

    assert validate_attestation(
        crystallized_state,
        active_state,
        attestation,
        block,
        parent_block,
        config,
    )


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,shard_count,'
        'attestation_slot'
    ),
    [
        (100, 1000, 50, 10, 10, 1),
        (100, 1000, 50, 10, 10, -1),
    ],
)
def test_validate_attestation_slot(attestation_validation_fixture, attestation_slot, config):
    (
        crystallized_state,
        active_state,
        attestation,
        block,
        parent_block
    ) = attestation_validation_fixture

    attestation.slot = attestation_slot
    with pytest.raises(ValidationError):
        validate_attestation(
            crystallized_state,
            active_state,
            attestation,
            block,
            parent_block,
            config,
        )


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,shard_count,'
    ),
    [
        (100, 1000, 50, 10, 10),
    ],
)
def test_validate_attestation_justified(attestation_validation_fixture, config):
    (
        crystallized_state,
        active_state,
        original_attestation,
        block,
        parent_block
    ) = attestation_validation_fixture

    # Case 1: attestation.justified_slot > crystallized_state.last_justified_slot
    attestation = copy.deepcopy(original_attestation)
    attestation.justified_slot = crystallized_state.last_justified_slot + 1
    with pytest.raises(ValidationError):
        validate_attestation(
            crystallized_state,
            active_state,
            attestation,
            block,
            parent_block,
            config,
        )

    # Case 2: justified_block_hash is not in canonical chain
    attestation = copy.deepcopy(original_attestation)
    attestation.justified_block_hash = b'\x11' * 32
    with pytest.raises(ValidationError):
        validate_attestation(
            crystallized_state,
            active_state,
            attestation,
            block,
            parent_block,
            config,
        )

    # Case 3: justified_slot doesn't match justified_block_hash
    attestation = copy.deepcopy(original_attestation)
    attestation.justified_slot = attestation.justified_slot - 1
    with pytest.raises(ValidationError):
        validate_attestation(
            crystallized_state,
            active_state,
            attestation,
            block,
            parent_block,
            config,
        )


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,shard_count'
    ),
    [
        (100, 1000, 50, 10, 10),
    ],
)
def test_validate_attestation_attester_bitfield(
        attestation_validation_fixture,
        config):
    (
        crystallized_state,
        active_state,
        original_attestation,
        block,
        parent_block
    ) = attestation_validation_fixture

    attestation = copy.deepcopy(original_attestation)
    attestation.attester_bitfield = get_empty_bitfield(10)
    with pytest.raises(ValidationError):
        validate_attestation(
            crystallized_state,
            active_state,
            attestation,
            block,
            parent_block,
            config,
        )

    attestation = copy.deepcopy(original_attestation)
    attestation_indices = get_attestation_indices(
        crystallized_state,
        attestation,
        config
    )
    last_bit = len(attestation_indices)
    attestation.attester_bitfield = set_voted(attestation.attester_bitfield, last_bit)

    with pytest.raises(ValidationError):
        validate_attestation(
            crystallized_state,
            active_state,
            attestation,
            block,
            parent_block,
            config,
        )


@pytest.mark.noautofixt  # Use the real BLS verification
@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,shard_count'
    ),
    [
        (100, 1000, 50, 10, 10),
    ],
)
def test_validate_attestation_aggregate_sig(attestation_validation_fixture, config):
    (
        crystallized_state,
        active_state,
        attestation,
        block,
        parent_block
    ) = attestation_validation_fixture

    attestation.aggregate_sig = [0, 0]

    with pytest.raises(ValidationError):
        validate_attestation(
            crystallized_state,
            active_state,
            attestation,
            block,
            parent_block,
            config,
        )


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,min_dynasty_length,shard_count'
    ),
    [
        (200, 200, 10, 20, 20, 25),
    ]
)
# sanity check test
def test_calculate_crosslink_rewards(genesis_crystallized_state,
                                     genesis_active_state,
                                     genesis_block,
                                     config,
                                     mock_make_attestations,
                                     mock_make_child):
    c = genesis_crystallized_state
    a = genesis_active_state
    block = genesis_block
    a.chain = Chain(head=block, blocks=[block])

    # progress past first cycle transition
    # rewards on the following cycle recalc will be based
    # on what happened during this cycle
    attestations = mock_make_attestations(
        (c, a),
        block,
        # enough attesters to get a reward but not form a crosslink
        attester_share=0.58
    )
    block2, c2, a2 = mock_make_child(
        (c, a),
        block,
        block.slot_number + config['cycle_length'],
        attestations
    )

    # attestation used for testing
    attestation = attestations[0]

    # create a block to trigger next cycle transition
    attestations2 = mock_make_attestations(
        (c2, a2),
        block2,
        attester_share=0.0
    )
    block3, c3, a3 = mock_make_child(
        (c2, a2),
        block2,
        block2.slot_number + config['cycle_length'],
        attestations2
    )

    rewards_and_penalties = calculate_crosslink_rewards(c2, a2, block3, config)

    shard_and_committee = get_shards_and_committees_for_slot(c2, block2.slot_number, config)[0]
    for committee_index, validator_index in enumerate(shard_and_committee.committee):
        if has_voted(attestation.attester_bitfield, committee_index):
            assert rewards_and_penalties[validator_index] > 0
        else:
            assert rewards_and_penalties[validator_index] < 0


@pytest.mark.parametrize(
    (
        'cycle_length,'
        'last_state_recalc,'
        'last_justified_slot,'
        'justified_streak,'
        'last_finalized_slot,'
        'fraction_voted,'
        'result_last_state_recalc,'
        'result_justified_streak,'
        'result_last_finalized_slot'
    ),
    [
        # 2/3 attestations
        (64, 0, 0, 0, 0, 2/3.0, 64, 0+64, 0),
        # 1/3 attestations
        (64, 0, 0, 0, 0, 1/3.0, 64, 0+0, 0),
        # 2/3 attestations, last_finalized_slot = slot - cycle_length - 1
        (64, 128, 128, 64, 0, 2/3.0, 128+64, 64+64, 127-64-1),
        # 2/3 attestations, last_finalized_slot = last_finalized_slot
        (64, 128, 128, 128, 128, 2/3.0, 128+64, 128+64, 128),
    ],
)
def test_initialize_new_cycle(genesis_crystallized_state,
                              genesis_active_state,
                              genesis_block,
                              last_state_recalc,
                              last_justified_slot,
                              justified_streak,
                              last_finalized_slot,
                              fraction_voted,
                              result_last_state_recalc,
                              result_justified_streak,
                              result_last_finalized_slot,
                              config):
    # Fill the parent_crystallized_state with parematers
    parent_crystallized_state = genesis_crystallized_state
    parent_crystallized_state.last_state_recalc = last_state_recalc
    parent_crystallized_state.last_justified_slot = last_justified_slot
    parent_crystallized_state.justified_streak = justified_streak
    parent_crystallized_state.last_finalized_slot = last_finalized_slot

    parent_active_state = genesis_active_state

    parent_block = genesis_block
    block = copy.deepcopy(genesis_block)
    block.slot_number = 258
    block.parent_hash = blake(serialize(parent_block))

    active_state = fill_recent_block_hashes(
        parent_active_state, parent_block, block
    )

    fraction_voted *= 1.01  # add margin for rounding error
    # Fill the total_voter_deposits to simulate the different committee results
    active_state.block_vote_cache[block.parent_hash] = {
        'voter_indices': set(),
        'total_voter_deposits': int(parent_crystallized_state.total_deposits * fraction_voted)
    }

    crystallized_state, active_state = initialize_new_cycle(
        parent_crystallized_state,
        active_state,
        block,
        config=config,
    )
    assert crystallized_state.last_state_recalc == result_last_state_recalc
    assert crystallized_state.justified_streak == result_justified_streak
    assert crystallized_state.last_finalized_slot == result_last_finalized_slot


def test_compute_cycle_transitions(genesis_crystallized_state,
                                   genesis_active_state,
                                   genesis_block,
                                   config):
    parent_crystallized_state = genesis_crystallized_state
    parent_active_state = genesis_active_state
    parent_block = genesis_block
    block = copy.deepcopy(genesis_block)
    block.slot_number = config['cycle_length'] * 3

    active_state = fill_recent_block_hashes(
        parent_active_state, parent_block, block
    )
    crystallized_state, active_state = compute_cycle_transitions(
        parent_crystallized_state,
        active_state,
        block,
        config=config,
    )
    assert crystallized_state.last_state_recalc == (
        block.slot_number // config['cycle_length'] * config['cycle_length']
    )
