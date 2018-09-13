import pytest

from beacon_chain.state.active_state import ActiveState
from beacon_chain.state.helpers import (
    get_new_shuffling,
    get_shard_and_committees_for_slot,
    get_block_hash,
)

from tests.state.helpers import (
    get_pseudo_chain,
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
    for slot_indices in shuffling:
        for shard_and_committee in slot_indices:
            shards.add(shard_and_committee.shard_id)
            for vi in shard_and_committee.committee:
                validators.add(vi)

    # assert len(shards) == config['shard_count']
    assert len(validators) == len(genesis_validators)


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
def test_get_new_shuffling_handles_shard_wrap(genesis_validators, config):
    dynasty = 1

    shuffling = get_new_shuffling(
        b'\x35'*32,
        genesis_validators,
        dynasty,
        config['shard_count'] - 1,
        config
    )

    # shard assignments should wrap around to 0 rather than continuing to SHARD_COUNT
    for slot_indices in shuffling:
        for shard_and_committee in slot_indices:
            assert shard_and_committee.shard_id < config['shard_count']


@pytest.mark.parametrize(
    (
        'num_validators,slot,success'
    ),
    [
        (100, 0, True),
        (100, 63, True),
        (100, 64, False),
    ],
)
def test_get_shard_and_committees_for_slot(
        genesis_crystallized_state,
        num_validators,
        slot,
        success,
        config):
    crystallized_state = genesis_crystallized_state

    if success:
        shard_and_committees_for_slot = get_shard_and_committees_for_slot(
            crystallized_state,
            slot,
            config=config,
        )
        assert len(shard_and_committees_for_slot) > 0
    else:
        with pytest.raises(AssertionError):
            get_shard_and_committees_for_slot(
                crystallized_state,
                slot,
                config=config,
            )


@pytest.mark.parametrize(
    (
        'current_block_number,slot,success'
    ),
    [
        (10, 0, True),
        (10, 9, True),
        (10, 10, False),
        (128, 0, True),
        (128, 127, True),
        (128, 128, False),
    ],
)
def test_get_block_hash(
        genesis_block,
        current_block_number,
        slot,
        success,
        config):
    cycle_length = config['cycle_length']

    blocks = get_pseudo_chain(cycle_length * 3)
    recent_block_hashes = [
            b'\x00' * 32
            for i
            in range(cycle_length * 2 - current_block_number)
        ] + [block.hash for block in blocks[:current_block_number]]
    active_state = ActiveState(
        recent_block_hashes=recent_block_hashes,
    )
    current_block = blocks[current_block_number]

    if success:
        block_hash = get_block_hash(
            active_state,
            current_block,
            slot,
            config=config,
        )
        assert block_hash == blocks[slot].hash
    else:
        with pytest.raises(AssertionError):
            get_block_hash(
                active_state,
                current_block,
                slot,
                config=config,
            )
