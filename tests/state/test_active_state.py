import pytest


from beacon_chain.state.active_state import (
    ActiveState
)
from beacon_chain.state.recent_proposer_record import (
    RecentProposerRecord
)
from beacon_chain.utils.simpleserialize import (
    eq
)


@pytest.mark.parametrize(
    'param,default_value',
    [
        ('height', 0),
        ('randao', b'\x00'*32),
        ('ffg_voter_bitfield', b''),
        ('recent_attesters', []),
        ('partial_crosslinks', []),
        ('total_skip_count', 0),
        ('recent_proposers', []),
    ]
)
def test_defaults(param, default_value, sample_active_state_params):
    del sample_active_state_params[param]
    active_state = ActiveState(**sample_active_state_params)

    assert getattr(active_state, param) == default_value


def test_recent_proposers(sample_active_state_params,
                          sample_recent_proposer_record_params):
    recent_proposer = RecentProposerRecord(**sample_recent_proposer_record_params)
    sample_active_state_params['recent_proposers'] = [recent_proposer]

    active_state = ActiveState(**sample_active_state_params)
    assert len(active_state.recent_proposers) == 1
    assert eq(active_state.recent_proposers[0], recent_proposer)
