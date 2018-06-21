from beacon_chain.state.state_transition import (
    SHARD_COUNT,
)


# TODO: move to config.py
NOTARIES_PER_CROSSLINK = 100


def get_crosslink_shards(crystallized_state):
    start_from = crystallized_state.next_shard
    count = len(crystallized_state.active_validators) // NOTARIES_PER_CROSSLINK
    if start_from + count <= SHARD_COUNT:
        return list(range(start_from, start_from + count))
    else:
        result = (
            list(range(start_from, SHARD_COUNT)) +
            list(range(start_from + count - SHARD_COUNT))
        )
        return result


def get_crosslink_notaries(crystallized_state, shard_id):
    crosslink_shards = get_crosslink_shards(crystallized_state)
    if shard_id not in crosslink_shards:
        return None
    all = len(crystallized_state.current_shuffling)
    start = all * crosslink_shards.index(shard_id) // len(crosslink_shards)
    end = all * (crosslink_shards.index(shard_id)+1) // len(crosslink_shards)
    return crystallized_state.current_shuffling[start: end]
