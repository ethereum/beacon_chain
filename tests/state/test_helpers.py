import pytest

from beacon_chain.state.helpers import (
    get_crosslink_shards,
    NOTARIES_PER_CROSSLINK,
)


def create_crystallized_state(genesis_crystallized_state, next_shard):
    crystallized_state = genesis_crystallized_state
    genesis_crystallized_state.next_shard = next_shard
    return crystallized_state


@pytest.mark.parametrize(
    'next_shard,expected',
    (
        (0, list(range(0, 10))),
        (10, list(range(10, 20))),
    ),
    ids=[
        'next_shard=0',
        'next_shard=10',
    ],
)
def test_get_crosslink_shards(
        monkeypatch,
        genesis_crystallized_state,
        next_shard,
        expected):
    crystallized_state = create_crystallized_state(
        genesis_crystallized_state,
        next_shard
    )
    count = len(crystallized_state.active_validators) // NOTARIES_PER_CROSSLINK
    shard_list = get_crosslink_shards(crystallized_state)
    assert len(shard_list) == count
    assert shard_list[0] == next_shard
    assert shard_list == expected


def test_get_crosslink_notaries():
    pass
