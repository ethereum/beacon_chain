from beacon_chain.state.recent_proposer_record import (
    RecentProposerRecord
)


def test_default_balance_delta():
    recent_proposer_record = RecentProposerRecord(
        index=10,
        randao_commitment=b'\x35'*32
    )

    assert recent_proposer_record.balance_delta == 0
