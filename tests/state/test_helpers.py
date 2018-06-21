import pytest

from beacon_chain.state.state_transition import (
    get_shuffling,
    SHARD_COUNT,
    DEFAULT_BALANCE,
    DEFAULT_SWITCH_DYNASTY,
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


def mock_validator_record(pubkey):
    return ValidatorRecord(
        pubkey=pubkey,
        withdrawal_shard=0,
        withdrawal_address=pubkey.to_bytes(32, 'big')[-20:],
        randao_commitment=b'\x55'*32,
        balance=DEFAULT_BALANCE,
        switch_dynasty=DEFAULT_SWITCH_DYNASTY
    )


@pytest.mark.parametrize(
    'next_shard,active_validators,expected',
    (
        (
            0,
            [mock_validator_record(pubkey=pubkey) for pubkey in range(1000)],
            list(range(0, 10))
        ),
        (
            10,
            [mock_validator_record(pubkey=pubkey) for pubkey in range(1000)],
            list(range(10, 20))
        ),
        (
            10,
            [mock_validator_record(pubkey=pubkey) for pubkey in range(10001)],
            list(range(10, 20)) + list(range(0, 10))
        ),
    ),
    ids=[
        'next_shard=0, 1000 validators',
        'next_shard=10, 1000 validators',
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
    crosslink_shards = get_crosslink_shards(crystallized_state)
    assert crosslink_shards[0] == next_shard
    assert crosslink_shards == expected

    # test get_crosslink_notaries
    notaries = get_crosslink_notaries(crystallized_state, next_shard)
    assert len(notaries) == \
        len(crystallized_state.active_validators) // crosslink_shard_count


@pytest.mark.parametrize(
    'next_shard,exception',
    (
        (SHARD_COUNT+1, ValueError),
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
