import pytest

from beacon_chain.state.helpers import (
    get_new_shuffling
)


@pytest.mark.parametrize(
    (
        'num_validators,max_validator_count,cycle_length,'
        'min_committee_size,shard_count'
    ),
    [
        (1000, 1000, 20, 10, 100),
        (100, 500, 50, 10, 10),
        (20, 100, 10, 3, 10),
    ],
)
def test_get_new_shuffling_is_complete(genesis_validators, config):
    dynasty = 1

    shuffling = get_new_shuffling(
        b'\x35'*32,
        genesis_validators,
        dynasty,
        0,
        config
    )

    assert len(shuffling) == config['cycle_length']

    validators = set()
    shards = set()
    for height_indices in shuffling:
        for shard_and_committee in height_indices:
            shards.add(shard_and_committee.shard_id)
            for vi in shard_and_committee.committee:
                validators.add(vi)

    # assert len(shards) == config['shard_count']
    assert len(validators) == len(genesis_validators)
