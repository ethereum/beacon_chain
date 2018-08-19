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
        ('pending_attestations', []),
        ('recent_block_hashes', []),
    ]
)
def test_defaults(param, default_value, sample_active_state_params):
    del sample_active_state_params[param]
    active_state = ActiveState(**sample_active_state_params)

    assert getattr(active_state, param) == default_value


@pytest.mark.parametrize(
    'expected', [(0), (1), (5)]
)
def test_num_pending_attestations(expected):
    attestations = [AttestationRecord() for i in range(expected)]
    active_state = ActiveState(
        pending_attestations=attestations,
    )

    assert active_state.num_pending_attestations == expected


@pytest.mark.parametrize(
    'block_vote_cache',
    [
        (None),
        ({}),
        ({'a': 'b'}),
        ({1: 10, 10: 100})
    ]
)
def test_block_vote_cache(block_vote_cache):
    if block_vote_cache is None:
        active_state = ActiveState()
        assert active_state.block_vote_cache == {}
        return

    active_state = ActiveState(block_vote_cache=block_vote_cache)
    assert active_state.block_vote_cache == block_vote_cache
