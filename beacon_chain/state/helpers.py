from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)


def get_shuffling(seed, validator_count, sample=None, config=DEFAULT_CONFIG):
    max_validators = config['max_validators']
    assert validator_count <= max_validators

    if validator_count == 0:
        return []

    rand_max = max_validators - max_validators % validator_count
    o = list(range(validator_count))
    source = seed
    i = 0
    maxvalue = sample if sample is not None else validator_count
    while i < maxvalue:
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
    return o[:maxvalue]


def get_attesters_and_proposer(crystallized_state,
                               active_state,
                               skip_count,
                               config=DEFAULT_CONFIG):
    attester_count = config['attester_count']
    attestation_count = min(len(crystallized_state.active_validators), attester_count)

    indices = get_shuffling(
        active_state.randao,
        len(crystallized_state.active_validators),
        attestation_count + skip_count + 1,
        config
    )
    return indices[:attestation_count], indices[-1]


def get_crosslink_shards_count(active_validators_count, config=DEFAULT_CONFIG):
    """Returns the number of shards in the `crosslink_shards` list
    """
    shard_count = config['shard_count']
    crosslink_shards_count = (
        active_validators_count // config['notaries_per_crosslink']
    )
    if crosslink_shards_count > shard_count:
        crosslink_shards_count = shard_count
    return crosslink_shards_count


def get_crosslink_shards(crystallized_state, config=DEFAULT_CONFIG):
    """Returns a list of shards that will be crosslinked
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
