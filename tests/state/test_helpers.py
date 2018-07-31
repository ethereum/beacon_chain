import pytest

from beacon_chain.state.helpers import (
    get_crosslink_shards,
    get_crosslink_notaries,
    get_crosslink_shards_count,
    get_cutoffs,
)

from tests.state.helpers import (
    mock_crystallized_state,
    mock_validator_record,
)


def test_get_cutoffs():
    get_cutoffs(10)


@pytest.mark.parametrize(
    'active_validators_count, shard_count, notaries_per_crosslink, expected',
    (
        (1000, 20, 100, 10),
        (10000, 20, 100, 20),
        (50, 100, 3, 16),
    )
)
def test_get_crosslink_shards_count(active_validators_count,
                                    shard_count,
                                    notaries_per_crosslink,
                                    expected,
                                    config):
    crosslink_shards_count = get_crosslink_shards_count(
        active_validators_count,
        config=config,
    )
    assert crosslink_shards_count == expected


@pytest.mark.parametrize(
    'next_shard,shard_count,notaries_per_crosslink,num_validators,expected',
    (
        (0, 20, 100, 1000, list(range(0, 10))),
        (10, 20, 100, 1000, list(range(10, 20))),
        (19, 20, 100, 1000, [19] + list(range(0, 9))),
        (10, 20, 100, 10001, list(range(10, 20)) + list(range(0, 10))),
    ),
    ids=[
        'next_shard=0, 1000 validators',
        'next_shard=10, 1000 validators',
        'next_shard=19, 1000 validators',
        'next_shard=10, 10001 validators',
    ],
)
def test_get_crosslink_shards_and_get_crosslink_notaries(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard,
        shard_count,
        notaries_per_crosslink,
        num_validators,
        expected,
        config):
    active_validators = [
        mock_validator_record(pubkey, config)
        for pubkey in range(num_validators)
    ]
    crystallized_state = mock_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard,
        active_validators,
        config=config,
    )
    crosslink_shard_count = get_crosslink_shards_count(
        crystallized_state.num_active_validators
    )

    # test get_crosslink_shards
    crosslink_shards = get_crosslink_shards(
        crystallized_state,
        config=config,
    )
    assert crosslink_shards[0] == next_shard
    assert crosslink_shards == expected

    # test get_crosslink_notaries
    notaries = get_crosslink_notaries(
        crystallized_state,
        next_shard,
        config=config,
    )
    assert len(notaries) == \
        crystallized_state.num_active_validators // crosslink_shard_count


@pytest.mark.parametrize(
    'next_shard, shard_count, exception',
    [
        (21, 20, ValueError)
    ]
)
def test_get_crosslink_shards_error(genesis_crystallized_state,
                                    init_shuffling_seed,
                                    next_shard,
                                    shard_count,
                                    exception,
                                    config):
    crystallized_state = mock_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard
    )
    with pytest.raises(exception):
        get_crosslink_shards(crystallized_state, config=config)
