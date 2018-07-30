import pytest


from beacon_chain.state.active_state import (
    ActiveState
)


@pytest.mark.parametrize(
    'param,default_value',
    [
        ('total_attester_deposits', 0),
        ('attester_bitfield', b''),
    ]
)
def test_defaults(param, default_value, sample_active_state_params):
    del sample_active_state_params[param]
    active_state = ActiveState(**sample_active_state_params)

    assert getattr(active_state, param) == default_value
