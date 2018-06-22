import pytest

from beacon_chain.state.state_transition import (
    get_shuffling,
)
from beacon_chain.state.validator_record import (
    ValidatorRecord,
)
from beacon_chain.state.helpers import (
    get_crosslink_shards,
    get_crosslink_notaries,
    get_crosslink_shards_count,
)


def create_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard,
        active_validators=None):
    crystallized_state = genesis_crystallized_state
    crystallized_state.next_shard = next_shard
    if active_validators is not None:
        crystallized_state.active_validators = active_validators
        crystallized_state.current_shuffling = get_shuffling(
            init_shuffling_seed,
            len(active_validators),
        )
    return crystallized_state


def mock_validator_record(pubkey, config):
    return ValidatorRecord(
        pubkey=pubkey,
        withdrawal_shard=0,
        withdrawal_address=pubkey.to_bytes(32, 'big')[-20:],
        randao_commitment=b'\x55'*32,
        balance=config['default_balance'],
        switch_dynasty=config['default_switch_dynasty']
    )


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
    crystallized_state = create_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard,
        active_validators,
    )
    crosslink_shard_count = get_crosslink_shards_count(
        len(crystallized_state.active_validators)
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
        len(crystallized_state.active_validators) // crosslink_shard_count


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
    crystallized_state = create_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard
    )
    with pytest.raises(exception):
        get_crosslink_shards(crystallized_state, config=config)
