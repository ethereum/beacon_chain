import copy

import pytest

from beacon_chain.state.state_transition import (
    get_recalculated_states,
    fill_recent_block_hashes,
    validate_attestation,
)


@pytest.mark.parametrize(
    'attestation_slot,block_slot_number,is_valid',
    [
        (5, 4, False),
        (6, 6, False),
        (6, 7, True),
        (1, 10, True),
    ]
)
def test_validate_attestation_slot(attestation_slot,
                                   block_slot_number,
                                   is_valid,
                                   sample_attestation_record_params,
                                   sample_block_params,
                                   sample_crystallized_state_params):
    pass


def test_validate_attestation_bitfield():
    pass


def test_validate_attestation_aggregate_sig():
    pass


def test_get_recalculated_states(genesis_block,
                                 genesis_crystallized_state,
                                 genesis_active_state,
                                 config):
    parent_crystallized_state = genesis_crystallized_state
    parent_active_state = genesis_active_state
    parent_block = genesis_block
    block = copy.deepcopy(genesis_block)
    block.slot_number = 258

    active_state = fill_recent_block_hashes(
        parent_active_state, parent_block, block
    )
    crystallized_state, active_state = get_recalculated_states(
        block,
        parent_crystallized_state,
        active_state,
        config=config,
    )
    assert crystallized_state.last_state_recalc == (
        block.slot_number // config['cycle_length'] * config['cycle_length']
    )
