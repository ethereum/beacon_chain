import pytest

from beacon_chain.utils.blake import blake

from beacon_chain.state.active_state import ActiveState
from beacon_chain.state.block import Block
from beacon_chain.state.helpers import (
    get_new_shuffling,
    get_indices_for_slot,
    get_block_hash,
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
    print([
        [j.committee 
        for j in item]
        for item in shuffling]
    )
    print('shuffling: {}'.format(shuffling))
    validators = set()
    shards = set()
    for height_indices in shuffling:
        for shard_and_committee in height_indices:
            shards.add(shard_and_committee.shard_id)
            for vi in shard_and_committee.committee:
                validators.add(vi)

    # assert len(shards) == config['shard_count']
    assert len(validators) == len(genesis_validators)


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
def test_get_indices_for_slot(
        genesis_crystallized_state,
        num_validators,
        slot,
        success,
        config):
    crystallized_state = genesis_crystallized_state

    if success:
        indices_for_slot = get_indices_for_slot(
            crystallized_state,
            slot,
            config=config,
        )
        assert len(indices_for_slot) > 0
    else:
        with pytest.raises(AssertionError):
            get_indices_for_slot(
                crystallized_state,
                slot,
                config=config,
            )


@pytest.mark.parametrize(
    (
        'slot,success'
    ),
    [
        (0, True),
        (127, True),
        (128, False),
    ],
)
def test_get_block_hash(
        genesis_block,
        slot,
        success,
        config):
    cycle_length = config['cycle_length']

    blocks = get_empty_chain(cycle_length * 3)
    active_state = ActiveState(
        recent_block_hashes=[block.hash for block in blocks[:cycle_length*2]]
    )
    if success:
        block_hash = get_block_hash(
            active_state,
            blocks[cycle_length*2],
            slot,
            config=config,
        )
        assert block_hash == blocks[slot].hash
    else:
        with pytest.raises(AssertionError):
            get_block_hash(
                active_state,
                blocks[cycle_length*2],
                slot,
                config=config,
            )


def get_empty_chain(length):
    blocks = []
    for slot in range(length * 3):
        blocks.append(
            Block(
                slot_number=slot,
                parent_hash=blocks[slot-1].hash if slot > 0 else b'00'*32
            )
        )

    return blocks
