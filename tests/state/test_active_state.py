import pytest


from beacon_chain.state.active_state import (
    ActiveState,
)
from beacon_chain.state.attestation_record import (
    AttestationRecord,
)


@pytest.mark.parametrize(
    'param,default_value',
    [
        ('attestations', []),
        ('total_attester_deposits', 0),
        ('attester_bitfield', b''),
    ]
)
def test_defaults(param, default_value, sample_active_state_params):
    del sample_active_state_params[param]
    active_state = ActiveState(**sample_active_state_params)

    assert getattr(active_state, param) == default_value


@pytest.mark.parametrize(
    'expected', [(0), (1), (5)]
)
def test_num_attestations(expected):
    attestations = [AttestationRecord() for i in range(expected)]
    active_state = ActiveState(
        attestations=attestations,
    )

    assert active_state.num_attestations == expected
