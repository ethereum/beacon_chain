from typing import (
    Any,
    Dict,
    List,
    TYPE_CHECKING,
)

from beacon_chain.beacon_typing.custom import (
    Hash32,
    ShardId,
)

from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)
from beacon_chain.state.shard_and_committee import (
    ShardAndCommittee,
)
from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.utils.simpleserialize import (
    serialize,
)


if TYPE_CHECKING:
    from .active_state import ActiveState  # noqa: F401
    from .attestation import AttestationRecord  # noqa: F401
    from .block import Block  # noqa: F401
    from .crystallized_state import CrystallizedState  # noqa: F401
    from .validator_record import ValidatorRecord  # noqa: F401


def is_power_of_two(num: int) -> bool:
    return ((num & (num - 1)) == 0) and num != 0


# Given the head block to attest to, collect the list of hashes to be
# signed in the attestation
def get_hashes_to_sign(active_state: 'ActiveState',
                       block: 'Block',
                       config: Dict[str, Any]=DEFAULT_CONFIG) -> List[Hash32]:
    cycle_length = config['cycle_length']

    hashes = get_hashes_from_active_state(
        active_state,
        block,
        from_slot=block.slot_number - cycle_length + 1,
        to_slot=block.slot_number - 1,
        config=config,
    ) + [blake(serialize(block))]

    return hashes


# Given an attestation and the block they were included in,
# the list of hashes that were included in the signature
def get_signed_parent_hashes(active_state: 'ActiveState',
                             block: 'Block',
                             attestation: 'AttestationRecord',
                             config: Dict[str, Any]=DEFAULT_CONFIG) -> List[Hash32]:
    cycle_length = config['cycle_length']
    parent_hashes = get_hashes_from_active_state(
        active_state,
        block,
        from_slot=attestation.slot - cycle_length + 1,
        to_slot=attestation.slot - len(attestation.oblique_parent_hashes),
        config=config,
    ) + attestation.oblique_parent_hashes

    return parent_hashes


def get_hashes_from_active_state(active_state: 'ActiveState',
                                 block: 'Block',
                                 from_slot: int,
                                 to_slot: int,
                                 config: Dict[str, Any]=DEFAULT_CONFIG) -> List[Hash32]:
    hashes = [
        get_block_hash(
            active_state,
            block,
            slot,
            config,
        )
        for slot
        in range(from_slot, to_slot + 1)
    ]
    return hashes


def get_attestation_indices(crystallized_state: 'CrystallizedState',
                            attestation: 'AttestationRecord',
                            config: Dict[str, Any]=DEFAULT_CONFIG) -> List[int]:
    shard_id = attestation.shard_id

    filtered_indices_for_slot = list(
        filter(
            lambda x: x.shard_id == shard_id,
            get_indices_for_slot(
                crystallized_state,
                attestation.slot,
                config=config,
            )
        )
    )

    attestation_indices = []  # type: List[int]
    if filtered_indices_for_slot:
        attestation_indices = filtered_indices_for_slot[0].committee

    return attestation_indices


def get_new_recent_block_hashes(old_block_hashes: List[Hash32],
                                parent_slot: int,
                                current_slot: int,
                                parent_hash: Hash32) -> List[Hash32]:
    d = current_slot - parent_slot
    return old_block_hashes[d:] + [parent_hash] * min(d, len(old_block_hashes))


def get_active_validator_indices(dynasty: int,
                                 validators: List['ValidatorRecord']) -> List[int]:
    o = []
    for index, validator in enumerate(validators):
        if (validator.start_dynasty <= dynasty and dynasty < validator.end_dynasty):
            o.append(index)
    return o


def shuffle(lst: List[Any],
            seed: Hash32,
            config: Dict[str, Any]=DEFAULT_CONFIG) -> List[Any]:
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


def split(lst: List[Any], N: int) -> List[Any]:
    list_length = len(lst)
    return [
        lst[(list_length * i // N): (list_length * (i+1) // N)] for i in range(N)
    ]


def get_new_shuffling(seed: Hash32,
                      validators: List['ValidatorRecord'],
                      dynasty: int,
                      crosslinking_start_shard: ShardId,
                      config: Dict[str, Any]=DEFAULT_CONFIG) -> List[List[ShardAndCommittee]]:
    cycle_length = config['cycle_length']
    min_committee_size = config['min_committee_size']
    shard_count = config['shard_count']
    avs = get_active_validator_indices(dynasty, validators)
    if len(avs) >= cycle_length * min_committee_size:
        committees_per_slot = len(avs) // cycle_length // (min_committee_size * 2) + 1
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
    for slot, slot_indices in enumerate(validators_per_slot):
        shard_indices = split(slot_indices, committees_per_slot)
        shard_id_start = crosslinking_start_shard + slot * committees_per_slot // slots_per_committee
        o.append([ShardAndCommittee(
            shard_id=(shard_id_start + j) % shard_count,
            committee=indices
        ) for j, indices in enumerate(shard_indices)])
    return o


def get_indices_for_slot(
        crystallized_state: 'CrystallizedState',
        slot: int,
        config: Dict[str, Any]=DEFAULT_CONFIG) -> List[ShardAndCommittee]:
    cycle_length = config['cycle_length']

    start = crystallized_state.last_state_recalc - cycle_length
    assert start <= slot < start + cycle_length * 2
    return crystallized_state.shard_and_committee_for_slots[slot - start]


def get_block_hash(
        active_state: 'ActiveState',
        current_block: 'Block',
        slot: int,
        config: Dict[str, Any]=DEFAULT_CONFIG) -> Hash32:
    cycle_length = config['cycle_length']

    sback = current_block.slot_number - cycle_length * 2
    assert sback <= slot < sback + cycle_length * 2
    return active_state.recent_block_hashes[slot - sback]
