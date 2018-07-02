import pytest

import secrets

from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)
from beacon_chain.state.validator_record import (
    ValidatorRecord,
)
from beacon_chain.state.helpers import (
    get_attesters_and_proposer,
    get_crosslink_shards,
    get_crosslink_notaries,
    get_crosslink_shards_count,
    get_shuffling,
)

from tests.state.helpers import (
    mock_crystallized_state,
    mock_validator_record,
)

def test_get_shuffling():
    assert get_shuffling(b"\x00", 0) == []
    assert get_shuffling(b"\x00", 1) == [0]
    assert get_shuffling(b"\x03", 1) == [0]
    assert get_shuffling(b"\x00", 2) == [0, 1]
    assert get_shuffling(b"\x03", 2) == [1, 0]


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


@pytest.mark.skip
def test_get_attesters_and_proposer(genesis_crystallized_state,
                                    genesis_active_state):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state

    original_attesters, original_proposer = get_attesters_and_proposer(
        crystallized_state,
        active_state,
        skip_count=0,
    )
    assert 0 <= original_proposer < crystallized_state.num_active_validators
    assert all(0 <= i < crystallized_state.num_active_validators for i in original_attesters)
    assert len(original_attesters) == DEFAULT_CONFIG['attester_count']

    skip_attesters, skip_proposer = get_attesters_and_proposer(
        genesis_crystallized_state,
        genesis_active_state,
        skip_count=1,
    )
    assert skip_attesters == original_attesters
    assert skip_proposer != original_proposer

    active_state.randao = secrets.token_bytes(32)
    reshuffled_attesters, reshuffled_proposer = get_attesters_and_proposer(
        crystallized_state,
        active_state,
        skip_count=0
    )
    assert reshuffled_attesters != original_attesters
    assert reshuffled_proposer != original_proposer

    crystallized_state.active_validators = crystallized_state.active_validators[:3]
    assert crystallized_state.num_active_validators == 3
    few_attesters, few_proposer = get_attesters_and_proposer(
        crystallized_state,
        active_state,
        skip_count=0
    )
    assert len(few_attesters) == 3
    assert set(few_attesters) == {0, 1, 2}
    assert 0 <= few_proposer < 3
