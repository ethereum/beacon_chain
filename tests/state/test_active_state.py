import pytest


from beacon_chain.state.active_state import (
    ActiveState
)


@pytest.mark.parametrize(
    'param,default_value',
    [
        ('height', 0),
        ('randao', b'\x00'*32),
        ('ffg_voter_bitfield', b''),
        ('balance_deltas', []),
        ('partial_crosslinks', []),
        ('total_skip_count', 0),
    ]
)
def test_defaults(param, default_value, sample_active_state_params):
    del sample_active_state_params[param]
    active_state = ActiveState(**sample_active_state_params)

    assert getattr(active_state, param) == default_value
