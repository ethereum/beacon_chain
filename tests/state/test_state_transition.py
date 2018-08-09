import pytest

from beacon_chain.state.state_transition import (
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
