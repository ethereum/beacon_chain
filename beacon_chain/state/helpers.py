from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)


def get_shuffling(seed, validator_count, config=DEFAULT_CONFIG):
    assert validator_count <= 2**24

    rand_max = 2**24 - 2**24 % validator_count
    o = list(range(validator_count))
    source = seed
    i = 0
    while i < validator_count:
        source = blake(source)
        for pos in range(0, 30, 3):
            m = int.from_bytes(source[pos:pos+3], 'big')
            remaining = validator_count - i
            if remaining == 0:
                break
            if validator_count < rand_max:
                replacement_pos = (m % remaining) + i
                o[i], o[replacement_pos] = o[replacement_pos], o[i]
                i += 1
    return o


def get_cutoffs(validator_count, config=DEFAULT_CONFIG):
    height_cutoffs = [0]
    cofactor = 19
    STANDARD_COMMITTEE_SIZE = config['max_validator_count'] // config['shard_count']
    # If there are not enough validators to fill a minimally
    # sized committee at every height, skip some heights
    if validator_count < config['epoch_length'] * config['min_committee_size']:
        height_count = validator_count // config['min_committee_size'] or 1
        heights = [(i * cofactor) % config['epoch_length']
                   for i in range(height_count)]
    # If there are enough validators, fill all the heights
    else:
        height_count = config['epoch_length']
        heights = list(range(config['epoch_length']))

    filled = 0
    for i in range(config['epoch_length'] - 1):
        if not i in heights:
            height_cutoffs.append(height_cutoffs[-1])
        else:
            filled += 1
            height_cutoffs.append(filled * validator_count // height_count)
    height_cutoffs.append(validator_count)

    # For the validators assigned to each height, split them up
    # into committees for different shards. Do not assign the
    # last END_EPOCH_GRACE_PERIOD heights in an epoch to any shards.
    shard_cutoffs = [0]
    for i in range(config['epoch_length'] - config['end_epoch_grace_period']):
        size = height_cutoffs[i+1] - height_cutoffs[i]
        shards = (size + STANDARD_COMMITTEE_SIZE - 1) // STANDARD_COMMITTEE_SIZE
        pre = shard_cutoffs[-1]
        for j in range(1, shards+1):
            shard_cutoffs.append(pre + size * j // shards)

    return height_cutoffs, shard_cutoffs


def get_crosslink_shards_count(active_validators_count, config=DEFAULT_CONFIG):
    """Returns how many shards in the `crosslink_shards` list
    """
    shard_count = config['shard_count']
    crosslink_shards_count = (
        active_validators_count // config['notaries_per_crosslink']
    )
    if crosslink_shards_count > shard_count:
        crosslink_shards_count = shard_count
    return crosslink_shards_count


def get_crosslink_shards(crystallized_state, config=DEFAULT_CONFIG):
    """Returns a list of shards that will be crosslinking
    """
    shard_count = config['shard_count']
    start_from = crystallized_state.next_shard
    if start_from >= shard_count:
        raise ValueError(
            'start_from %d is larger than SHARD_COUNT %d',
            start_from,
            shard_count,
        )

    crosslink_shards_count = get_crosslink_shards_count(
        crystallized_state.num_active_validators,
        config=config,
    )

    if start_from + crosslink_shards_count <= shard_count:
        return list(range(start_from, start_from + crosslink_shards_count))
    else:
        result = (
            list(range(start_from, shard_count)) +
            list(range(start_from + crosslink_shards_count - shard_count))
        )
        return result


def get_crosslink_notaries(
        crystallized_state,
        shard_id,
        crosslink_shards=None,
        config=DEFAULT_CONFIG):
    """Returns a list of notaries that will notarize `shard_id`
    """
    if crosslink_shards is None:
        crosslink_shards = get_crosslink_shards(
            crystallized_state,
            config=config,
        )
    num_crosslink_shards = len(crosslink_shards)

    if shard_id not in crosslink_shards:
        return None

    num_active_validators = crystallized_state.num_active_validators

    start = (
        num_active_validators * crosslink_shards.index(shard_id) //
        num_crosslink_shards
    )
    end = (
        num_active_validators * (crosslink_shards.index(shard_id) + 1) //
        num_crosslink_shards
    )
    return crystallized_state.current_shuffling[start:end]
