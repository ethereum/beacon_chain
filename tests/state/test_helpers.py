import pytest

from beacon_chain.state.config import (
    generate_config,
)
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


# Fixed configuration for this test especially
REPLACED_PARAMETERS = {
    'shard_count': 20,
    'notaries_per_crosslink': 100,
}
testing_helpers_config = generate_config(
    shard_count=20,
    notaries_per_crosslink=100,
)


def create_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed, next_shard,
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


def mock_validator_record(pubkey, testing_helpers_config):
    return ValidatorRecord(
        pubkey=pubkey,
        withdrawal_shard=0,
        withdrawal_address=pubkey.to_bytes(32, 'big')[-20:],
        randao_commitment=b'\x55'*32,
        balance=testing_helpers_config['default_balance'],
        switch_dynasty=testing_helpers_config['default_switch_dynasty']
    )


@pytest.mark.parametrize(
    'active_validators_count, expected',
    (
        (1000, 10),
        (10000, testing_helpers_config['shard_count'])
    )
)
def test_get_crosslink_shards_count(active_validators_count, expected):
    crosslink_shards_count = get_crosslink_shards_count(
        active_validators_count,
        config=testing_helpers_config,
    )
    assert crosslink_shards_count == expected


@pytest.mark.parametrize(
    'next_shard, active_validators, expected',
    (
        (
            0,
            [
                mock_validator_record(pubkey, testing_helpers_config)
                for pubkey in range(1000)
            ],
            list(range(0, 10))
        ),
        (
            10,
            [
                mock_validator_record(pubkey, testing_helpers_config)
                for pubkey in range(1000)
            ],
            list(range(10, 20))
        ),
        (
            19,
            [
                mock_validator_record(pubkey, testing_helpers_config)
                for pubkey in range(1000)
            ],
            [19] + list(range(0, 9))
        ),
        (
            10,
            [
                mock_validator_record(pubkey, testing_helpers_config)
                for pubkey in range(10001)
            ],
            list(range(10, 20)) + list(range(0, 10))
        ),
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
        active_validators,
        expected):
    # TODO: fixing the protocol parameter configuration
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
        config=testing_helpers_config,
    )
    assert crosslink_shards[0] == next_shard
    assert crosslink_shards == expected

    # test get_crosslink_notaries
    notaries = get_crosslink_notaries(
        crystallized_state,
        next_shard,
        config=testing_helpers_config,
    )
    assert len(notaries) == \
        len(crystallized_state.active_validators) // crosslink_shard_count


@pytest.mark.parametrize(
    'next_shard, exception',
    (
        (testing_helpers_config['shard_count']+1, ValueError),
    ),
    ids=[
        'next_shard=SHARD_COUNT+1',
    ],
)
def test_get_crosslink_shards_error(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard,
        exception):
    crystallized_state = create_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard
    )
    with pytest.raises(exception):
        get_crosslink_shards(crystallized_state)
