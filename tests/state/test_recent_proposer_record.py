import pytest

from beacon_chain.state.recent_proposer_record import (
    RecentProposerRecord
)


@pytest.mark.parametrize(
    'param,default_value',
    [
        ('randao_commitment', b'\x00'*32),
        ('balance_delta', 0),
    ]
)
def test_defaults(param, default_value, sample_recent_proposer_record_params):
    del sample_recent_proposer_record_params[param]
    proposer = RecentProposerRecord(**sample_recent_proposer_record_params)

    assert getattr(proposer, param) == default_value
