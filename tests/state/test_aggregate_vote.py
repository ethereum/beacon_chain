from beacon_chain.state.aggregate_vote import (
    AggregateVote,
)


def test_num_properties():
    aggregate_vote = AggregateVote(
        aggregate_sig=list(range(3))
    )

    assert aggregate_vote.num_aggregate_sig == 3
