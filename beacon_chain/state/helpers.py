from beacon_chain.utils.blake import (
    blake,
)

from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)
from beacon_chain.state.shard_and_indices import (
    ShardAndIndices,
)


def get_active_validator_indices(dynasty, validators):
    o = []
    for i in range(len(validators)):
        if (validators[i].start_dynasty <= dynasty and dynasty < validators[i].end_dynasty):
            o.append(i)
    return o


def shuffle(lst,
            seed,
            config=DEFAULT_CONFIG):
    lst_count = len(lst)
    assert lst_count <= 16777216
    rand_max = 16777216 - 16777216 % lst_count
    o = [x for x in lst]
    source = seed
    i = 0
    while i < len(lst):
        source = blake(source)
        for pos in range(0, 30, 3):
            m = int.from_bytes(source[pos:pos+3], 'big')
            remaining = lst_count - i
            if remaining == 0:
                break
            if lst_count < rand_max:
                replacement_pos = (m % remaining) + i
                o[i], o[replacement_pos] = o[replacement_pos], o[i]
                i += 1
    return o


def split(lst, N):
    return [
        lst[(len(lst) * i // N): (len(lst) * (i+1) // N)] for i in range(N)
    ]


def get_new_shuffling(validators,
                      dynasty,
                      crosslinking_start_shard,
                      seed,
                      config=DEFAULT_CONFIG):
    epoch_length = config['epoch_length']
    min_committee_size = config['min_committee_size']
    avs = get_active_validator_indices(validators, dynasty)
    if len(avs) >= epoch_length * min_committee_size:
        committees_per_slot = int(len(avs) // epoch_length // (min_committee_size * 2)) + 1
        slots_per_committee = 1
    else:
        committees_per_slot = 1
        slots_per_committee = 1
        while (len(avs) * slots_per_committee < epoch_length * min_committee_size and
               slots_per_committee < epoch_length):
            slots_per_committee *= 2
    o = []
    for i, height_indices in enumerate(split(shuffle(avs, seed, config), epoch_length)):
        shard_indices = split(height_indices, committees_per_slot)
        o.append([ShardAndIndices(
            shard_id=(
                crosslinking_start_shard +
                i * committees_per_slot // slots_per_committee + j
            ),
            committee=indices
        ) for j, indices in enumerate(shard_indices)])
    return o
