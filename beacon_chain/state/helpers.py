from beacon_chain.state.state_transition import (
    SHARD_COUNT,
)


# TODO: move to config.py
NOTARIES_PER_CROSSLINK = 100


def get_crosslink_shards_count(active_validators_count):
    """Returns how many shards in the `crosslink_shards` list
    """
    crosslink_shards_count = active_validators_count // NOTARIES_PER_CROSSLINK
    if crosslink_shards_count > SHARD_COUNT:
        crosslink_shards_count = SHARD_COUNT
    return crosslink_shards_count


def get_crosslink_shards(crystallized_state):
    """Returns a list of shards that will be crosslinking
    """
    start_from = crystallized_state.next_shard
    if start_from >= SHARD_COUNT:
        raise ValueError(
            'start_from %d is larger than SHARD_COUNT %d',
            start_from,
            SHARD_COUNT,
        )

    crosslink_shards_count = get_crosslink_shards_count(
        len(crystallized_state.active_validators),
    )

    if start_from + crosslink_shards_count <= SHARD_COUNT:
        return list(range(start_from, start_from + crosslink_shards_count))
    else:
        result = (
            list(range(start_from, SHARD_COUNT)) +
            list(range(start_from + crosslink_shards_count - SHARD_COUNT))
        )
        return result


def get_crosslink_notaries(crystallized_state, shard_id):
    """Returns a list of notaries that will notaries `shard_id`
    """
    crosslink_shards = get_crosslink_shards(crystallized_state)
    if shard_id not in crosslink_shards:
        return None
    all = len(crystallized_state.current_shuffling)
    start = all * crosslink_shards.index(shard_id) // len(crosslink_shards)
    end = all * (crosslink_shards.index(shard_id)+1) // len(crosslink_shards)
    return crystallized_state.current_shuffling[start: end]
