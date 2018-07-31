import pytest

from beacon_chain.state.new_state_transition import (
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
                                   valid_attestation_params,
                                   valid_block_params,
                                   valid_crystallized_state_params):
    pass


def test_validate_attestation_checkpoint_hash():
    pass


def test_validate_attestation_shard_in_height_cutoffs():
    pass


def test_validate_attestation_in_end_grace_period():
    pass


def test_validate_attestation_bitfield():
    pass


def test_validate_attestation_aggregate_sig():
    pass
