from beacon_chain.utils.blake import (
    blake,
)

from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)
from beacon_chain.state.crosslink_record import (
    CrosslinkRecord,
)
from beacon_chain.state.shard_and_committee import (
    ShardAndCommittee,
)
from beacon_chain.utils.simpleserialize import (
    deepcopy,
)
from beacon_chain.utils.bitfield import (
    has_voted,
    or_bitfields,
)


def get_new_recent_block_hashes(old_block_hashes,
                                parent_slot,
                                current_slot,
                                parent_hash):
    d = current_slot - parent_slot
    return old_block_hashes[d:] + [parent_hash] * min(d, len(old_block_hashes))


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
    for i, height_indices in enumerate(split(shuffle(avs, seed, config), cycle_length)):
        shard_indices = split(height_indices, committees_per_slot)
        o.append([ShardAndCommittee(
            shard_id=(
                crosslinking_start_shard +
                i * committees_per_slot // slots_per_committee + j
            ),
            committee=indices
        ) for j, indices in enumerate(shard_indices)])
    return o


#
# Old code storage
#

# This is the old process crosslinks code
# processing crosslinks is currently not in the spec source
# I want to keep this around until we know what the spec looks like
def old_process_crosslinks(crystallized_state, active_state, shard_cutoffs, config=DEFAULT_CONFIG):
    #
    # Process crosslink roots and rewards
    #
    new_active_validators = deepcopy(crystallized_state.validators)
    new_crosslink_records = [crosslink for crosslink in crystallized_state.crosslink_records]
    for shard_id in range(config['shard_count']):
        attestations = filter(lambda a: a.shard_id == shard_id, active_state.attestations)
        roots = set(map(lambda a: a.shard_block_hash, attestations))
        start = shard_cutoffs[shard_id]
        end = shard_cutoffs[shard_id + 1]
        root_attester_bitfields = {}
        root_total_balance = {}
        best_root = b'\x00'*32
        best_root_deposit_size = 0

        # find best_root
        for root in roots:
            root_attestations = filter(lambda a: a.shard_block_hash == root, attestations)
            root_attester_bitfields[root] = or_bitfields(
                map(lambda a: a.attester_bitfield, root_attestations)
            )
            root_total_balance[root] = 0
            for i in range(end - start):
                if has_voted(root_attester_bitfields[root], i):
                    validator_index = crystallized_state.current_shuffling[start + i]
                    balance = crystallized_state.active_validators[validator_index].balance
                    root_total_balance[root] += balance

            if root_total_balance[root] > best_root_deposit_size:
                best_root = root
                best_root_deposit_size = root_total_balance[root]

        has_adequate_deposit = best_root_deposit_size * 3 >= crystallized_state.total_deposits * 2
        needs_new_crosslink = (
            crystallized_state.crosslink_records[shard_id].epoch <
            crystallized_state.last_finalized_epoch
        )
        if has_adequate_deposit and needs_new_crosslink:
            new_crosslink_records[shard_id] = CrosslinkRecord(
                hash=best_root,
                epoch=crystallized_state.current_epoch
            )
            for i in range(end - start):
                validator_index = crystallized_state.current_shuffling[start + i]
                if has_voted(root_attester_bitfields[best_root], i):
                    new_active_validators[validator_index].balance += config['online_crosslink_reward']
                else:
                    new_active_validators[validator_index].balance -= config['offline_crosslink_penalty']
