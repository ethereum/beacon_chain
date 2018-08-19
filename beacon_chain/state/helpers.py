from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)
from beacon_chain.state.shard_and_committee import (
    ShardAndCommittee,
)
from beacon_chain.utils.blake import (
    blake,
)


def is_power_of_two(num):
    return ((num & (num - 1)) == 0) and num != 0


def get_signed_parent_hashes(active_state,
                             block,
                             attestation,
                             config=DEFAULT_CONFIG):
    cycle_length = config['cycle_length']
    oblique_parent_hashes = attestation.oblique_parent_hashes

    parent_hashes = (
        active_state.recent_block_hashes[
            cycle_length + attestation.slot - block.slot_number:
            cycle_length * 2 + attestation.slot - block.slot_number - len(oblique_parent_hashes)
        ] +
        oblique_parent_hashes

    )
    return parent_hashes


def get_attestation_indices(crystallized_state,
                            attestation,
                            config=DEFAULT_CONFIG):
    last_state_recalc = crystallized_state.last_state_recalc
    cycle_length = config['cycle_length']
    indices_for_heights = crystallized_state.indices_for_heights

    shard_position = list(filter(
        lambda x: (
            indices_for_heights[attestation.slot - last_state_recalc + cycle_length][x].shard_id ==
            attestation.shard_id
        ),
        range(len(indices_for_heights[attestation.slot - last_state_recalc + cycle_length]))
    ))[0]
    attestation_indices = (
        indices_for_heights[
            attestation.slot - last_state_recalc + cycle_length
        ][shard_position].committee
    )

    return attestation_indices


def get_new_recent_block_hashes(old_block_hashes,
                                parent_slot,
                                current_slot,
                                parent_hash):
    d = current_slot - parent_slot
    return old_block_hashes[d:] + [parent_hash] * min(d, len(old_block_hashes))


def get_active_validator_indices(dynasty, validators):
    o = []
    for index, validator in enumerate(validators):
        if (validator.start_dynasty <= dynasty and dynasty < validator.end_dynasty):
            o.append(index)
    return o


def shuffle(lst,
            seed,
            config=DEFAULT_CONFIG):
    lst_count = len(lst)
    assert lst_count <= 16777216
    o = [x for x in lst]
    source = seed
    i = 0
    while i < lst_count:
        source = blake(source)
        for pos in range(0, 30, 3):
            m = int.from_bytes(source[pos:pos+3], 'big')
            remaining = lst_count - i
            if remaining == 0:
                break
            rand_max = 16777216 - 16777216 % remaining
            if m < rand_max:
                replacement_pos = (m % remaining) + i
                o[i], o[replacement_pos] = o[replacement_pos], o[i]
                i += 1
    return o


def split(lst, N):
    list_length = len(lst)
    return [
        lst[(list_length * i // N): (list_length * (i+1) // N)] for i in range(N)
    ]


def get_new_shuffling(seed,
                      validators,
                      dynasty,
                      crosslinking_start_shard,
                      config=DEFAULT_CONFIG):
    cycle_length = config['cycle_length']
    min_committee_size = config['min_committee_size']
    avs = get_active_validator_indices(dynasty, validators)
    if len(avs) >= cycle_length * min_committee_size:
        committees_per_slot = int(len(avs) // cycle_length // (min_committee_size * 2)) + 1
        slots_per_committee = 1
    else:
        committees_per_slot = 1
        slots_per_committee = 1
        while (len(avs) * slots_per_committee < cycle_length * min_committee_size and
               slots_per_committee < cycle_length):
            slots_per_committee *= 2
    o = []

    shuffled_active_validator_indices = shuffle(avs, seed, config)
    validators_per_slot = split(shuffled_active_validator_indices, cycle_length)
    for slot, height_indices in enumerate(validators_per_slot):
        shard_indices = split(height_indices, committees_per_slot)
        o.append([ShardAndCommittee(
            shard_id=(
                crosslinking_start_shard +
                slot * committees_per_slot // slots_per_committee + j
            ),
            committee=indices
        ) for j, indices in enumerate(shard_indices)])
    return o
