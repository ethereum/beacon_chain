from math import sqrt

from typing import (
    Any,
    Dict,
    List,
    Tuple,
    TYPE_CHECKING,
)

from ssz import (
    deepcopy,
)

from beacon_chain.beacon_typing.custom import (  # noqa: F401
    BlockVoteCache,
    Hash32,
    ShardId,
)

import beacon_chain.utils.bls as bls
from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.utils.bitfield import (
    get_bitfield_length,
    has_voted,
)

from .config import (
    DEFAULT_CONFIG,
)
from .active_state import (
    ActiveState,
)
from .chain import (
    Chain,
)
from .constants import (
    WEI_PER_ETH,
)
from .crosslink_record import (
    CrosslinkRecord,
)
from .crystallized_state import (
    CrystallizedState,
)
from .helpers import (
    get_active_validator_indices,
    get_attestation_indices,
    get_new_recent_block_hashes,
    get_new_shuffling,
    get_proposer_position,
    get_signed_parent_hashes,
)

if TYPE_CHECKING:
    from .attesation_record import AttestationRecord  # noqa: F401
    from .block import Block  # noqa: F401
    from .validator_record import ValidatorRecord  # noqa: F401


def validate_block_pre_processing_conditions(block: 'Block',
                   parent_block: 'Block',
                   crystallized_state: CrystallizedState,
                   config: Dict[str, Any]=DEFAULT_CONFIG) -> bool:
    # 1. ensure parent processed
    # 2. an attestation from the proposer of the block is included along with the block in the
    # network message object
    # 3. ensure pow_chain_ref processed
    # 4. ensure local time is large enough to process this block's slot

    return True


def validate_parent_block_proposer(block: 'Block',
                                   parent_block: 'Block',
                                   crystallized_state: CrystallizedState,
                                   config: Dict[str, Any]=DEFAULT_CONFIG) -> None:
    if block.slot_number == 0:
        return

    proposer_index_in_committee, shard_id = get_proposer_position(
        parent_block,
        crystallized_state,
        config=config,
    )

    assert len(block.attestations) > 0
    attestation = block.attestations[0]
    if not has_voted(attestation.attester_bitfield, proposer_index_in_committee):
        raise Exception(
            "Proposer of parent block should be one of the attesters in block.attestions[0]:"
            "proposer index in committee: %d" % proposer_index_in_committee
        )


def validate_attestation(crystallized_state: CrystallizedState,
                         active_state: ActiveState,
                         attestation: 'AttestationRecord',
                         block: 'Block',
                         parent_block: 'Block',
                         config: Dict[str, Any]=DEFAULT_CONFIG) -> None:
    # Verify attestation.slot_number
    if not attestation.slot <= parent_block.slot_number:
        raise Exception(
            "Attestation slot number too high:\n"
            "\tFound: %s Needed less than or equal to %s" %
            (attestation.slot, parent_block.slot_number)
        )
    if not (attestation.slot >= max(parent_block.slot_number - config['cycle_length'] + 1, 0)):
        raise Exception(
            "Attestation slot number too low:\n"
            "\tFound: %s, Needed greater than or equalt to: %s" %
            (
                attestation.slot,
                max(parent_block.slot_number - config['cycle_length'] + 1, 0)
            )
        )

    # TODO: Verify that the justified_slot and justified_block_hash given are in
    # the chain and are equal to or earlier than the last_justified_slot
    # in the crystallized state.

    parent_hashes = get_signed_parent_hashes(
        active_state,
        block,
        attestation,
        config
    )
    attestation_indices = get_attestation_indices(
        crystallized_state,
        attestation,
        config
    )

    #
    # validate bitfield
    #
    if not (len(attestation.attester_bitfield) == get_bitfield_length(len(attestation_indices))):
        raise Exception(
            "Attestation has incorrect bitfield length. Found: %s, Expected: %s" %
            (len(attestation.attester_bitfield), get_bitfield_length(len(attestation_indices)))
        )

    # check if end bits are zero
    last_bit = len(attestation_indices)
    if last_bit % 8 != 0:
        for i in range(8 - last_bit % 8):
            if has_voted(attestation.attester_bitfield, last_bit + i):
                raise Exception("Attestation has non-zero trailing bits")

    #
    # validate aggregate_sig
    #
    pub_keys = [
        crystallized_state.validators[index].pubkey
        for i, index in enumerate(attestation_indices)
        if has_voted(attestation.attester_bitfield, i)
    ]
    message = blake(
        attestation.slot.to_bytes(8, byteorder='big') +
        b''.join(parent_hashes) +
        attestation.shard_id.to_bytes(2, byteorder='big') +
        attestation.shard_block_hash +
        attestation.justified_slot.to_bytes(8, 'big')
    )
    if not bls.verify(message, bls.aggregate_pubs(pub_keys), attestation.aggregate_sig):
        raise Exception("Attestation aggregate signature fails")


def get_updated_block_vote_cache(crystallized_state: CrystallizedState,
                                 active_state: ActiveState,
                                 attestation: 'AttestationRecord',
                                 block: 'Block',
                                 block_vote_cache: BlockVoteCache,
                                 config: Dict[str, Any]=DEFAULT_CONFIG) -> BlockVoteCache:
    new_block_vote_cache = deepcopy(block_vote_cache)

    parent_hashes = get_signed_parent_hashes(
        active_state,
        block,
        attestation,
        config
    )
    attestation_indices = get_attestation_indices(
        crystallized_state,
        attestation,
        config
    )

    for parent_hash in parent_hashes:
        if parent_hash in attestation.oblique_parent_hashes:
            continue
        if parent_hash not in new_block_vote_cache:
            new_block_vote_cache[parent_hash] = {
                'voter_indices': set(),
                'total_voter_deposits': 0
            }
        for i, index in enumerate(attestation_indices):
            if (has_voted(attestation.attester_bitfield, i) and
                    index not in new_block_vote_cache[parent_hash]['voter_indices']):
                new_block_vote_cache[parent_hash]['voter_indices'].add(index)
                new_block_vote_cache[parent_hash]['total_voter_deposits'] += (
                    crystallized_state.validators[index].balance
                )

    return new_block_vote_cache


def process_block(crystallized_state: CrystallizedState,
                  active_state: ActiveState,
                  block: 'Block',
                  parent_block: 'Block',
                  config: dict = DEFAULT_CONFIG) -> ActiveState:
    new_block_vote_cache = deepcopy(active_state.block_vote_cache)

    validate_parent_block_proposer(block, parent_block, crystallized_state, config=config)

    for attestation in block.attestations:
        validate_attestation(crystallized_state,
                             active_state,
                             attestation,
                             block,
                             parent_block,
                             config)
        new_block_vote_cache = get_updated_block_vote_cache(
            crystallized_state,
            active_state,
            attestation,
            block,
            new_block_vote_cache,
            config
        )

    new_attestations = active_state.pending_attestations + block.attestations
    new_chain = Chain(
        head=block,
        blocks=active_state.chain.blocks + [block]
    )

    new_active_state = ActiveState(
        pending_attestations=new_attestations,
        recent_block_hashes=active_state.recent_block_hashes[:],
        block_vote_cache=new_block_vote_cache,
        chain=new_chain
    )
    return new_active_state


def process_updated_crosslinks(crystallized_state: CrystallizedState,
                               active_state: ActiveState,
                               block: 'Block',
                               config: Dict[str, Any]=DEFAULT_CONFIG) -> List[CrosslinkRecord]:
    total_attestation_balance = {}  # type: Dict[Tuple[ShardId, Hash32], int]

    crosslinks = deepcopy(crystallized_state.crosslink_records)

    for attestation in active_state.pending_attestations:
        shard_tuple = (attestation.shard_id, attestation.shard_block_hash)
        if shard_tuple not in total_attestation_balance:
            total_attestation_balance[shard_tuple] = 0

        attestation_indices = get_attestation_indices(
            crystallized_state,
            attestation,
            config
        )
        # find total committee size by balance
        total_committee_balance = sum([
            crystallized_state.validators[index].balance
            for index in attestation_indices
        ])
        # find votes cast in attestation by balance
        total_attestation_balance[shard_tuple] += sum([
            crystallized_state.validators[index].balance
            for in_cycle_slot_height, index in enumerate(attestation_indices)
            if has_voted(attestation.attester_bitfield, in_cycle_slot_height)
        ])

        # if 2/3 of committee voted on crosslink and do no yet have crosslink
        # for this shard, for this dynasty, add updated crosslink
        if (3 * total_attestation_balance[shard_tuple] >= 2 * total_committee_balance and
                crystallized_state.current_dynasty > crosslinks[attestation.shard_id].dynasty):
            crosslinks[attestation.shard_id] = CrosslinkRecord(
                dynasty=crystallized_state.current_dynasty,
                slot=crystallized_state.last_state_recalc + config['cycle_length'],
                hash=attestation.shard_block_hash
            )
    return crosslinks


def initialize_new_cycle(crystallized_state: CrystallizedState,
                         active_state: ActiveState,
                         block: 'Block',
                         config: Dict[str, Any]=DEFAULT_CONFIG
                         ) -> Tuple[CrystallizedState, ActiveState]:
    cycle_length = config['cycle_length']
    last_state_recalc = crystallized_state.last_state_recalc
    last_justified_slot = crystallized_state.last_justified_slot
    last_finalized_slot = crystallized_state.last_finalized_slot
    justified_streak = crystallized_state.justified_streak

    total_deposits = crystallized_state.total_deposits

    # walk through slots last_state_recalc - CYCLE_LENGTH ... last_state_recalc - 1
    # and check for justification, streaks, and finality
    for i in range(cycle_length):
        slot = i + (last_state_recalc - cycle_length)

        block_hash = active_state.recent_block_hashes[i]
        if block_hash in active_state.block_vote_cache:
            vote_balance = active_state.block_vote_cache[block_hash]['total_voter_deposits']
        else:
            vote_balance = 0

        if 3 * vote_balance >= 2 * total_deposits:
            last_justified_slot = max(last_justified_slot, slot)
            justified_streak += 1
        else:
            justified_streak = 0

        if justified_streak >= cycle_length + 1:
            last_finalized_slot = max(last_finalized_slot, slot - cycle_length - 1)

    crosslink_records = process_updated_crosslinks(
        crystallized_state,
        active_state,
        block,
        config
    )

    # remove attestations older than last_state_recalc
    pending_attestations = [
        a for a in active_state.pending_attestations
        if a.slot >= last_state_recalc
    ]

    validators = apply_rewards_and_penalties(
        crystallized_state,
        active_state,
        block,
        config=config
    )

    shard_and_committee_for_slots = (
        crystallized_state.shard_and_committee_for_slots[cycle_length:] +
        # this is a stub and will be addressed by shuffling at dynasty change
        crystallized_state.shard_and_committee_for_slots[cycle_length:]
    )

    new_crystallized_state = CrystallizedState(
        validators=validators,
        last_state_recalc=last_state_recalc + cycle_length,
        shard_and_committee_for_slots=shard_and_committee_for_slots,
        last_justified_slot=last_justified_slot,
        justified_streak=justified_streak,
        last_finalized_slot=last_finalized_slot,
        current_dynasty=crystallized_state.current_dynasty,
        crosslink_records=crosslink_records,
        dynasty_seed=crystallized_state.dynasty_seed,
        dynasty_start=crystallized_state.dynasty_start
    )

    new_active_state = ActiveState(
        pending_attestations=pending_attestations,
        recent_block_hashes=active_state.recent_block_hashes[:],
        # Should probably clean up block_vote_cache but old records won't break cache
        # so okay for now
        block_vote_cache=deepcopy(active_state.block_vote_cache)
    )

    return new_crystallized_state, new_active_state


def fill_recent_block_hashes(active_state: ActiveState,
                             parent_block: 'Block',
                             block: 'Block') -> ActiveState:
    return ActiveState(
        pending_attestations=deepcopy(active_state.pending_attestations),
        recent_block_hashes=get_new_recent_block_hashes(
            active_state.recent_block_hashes,
            parent_block.slot_number,
            block.slot_number,
            block.parent_hash
        ),
        block_vote_cache=deepcopy(active_state.block_vote_cache)
    )


def calculate_ffg_rewards(crystallized_state: CrystallizedState,
                          active_state: ActiveState,
                          block: 'Block',
                          config: Dict[str, Any]=DEFAULT_CONFIG) -> List[int]:
    validators = crystallized_state.validators
    active_validator_indices = get_active_validator_indices(
        crystallized_state.current_dynasty,
        validators
    )
    rewards_and_penalties = [0 for _ in validators]  # type: List[int]

    time_since_finality = block.slot_number - crystallized_state.last_finalized_slot
    total_deposits = crystallized_state.total_deposits
    total_deposits_in_ETH = total_deposits // WEI_PER_ETH
    reward_quotient = config['base_reward_quotient'] * int(sqrt(total_deposits_in_ETH))
    quadratic_penalty_quotient = int(sqrt(config['sqrt_e_drop_time'] / config['slot_duration']))

    last_state_recalc = crystallized_state.last_state_recalc
    block_vote_cache = active_state.block_vote_cache

    for slot in range(last_state_recalc - config['cycle_length'], last_state_recalc):
        block = active_state.chain.get_block_by_slot_number(slot)
        if block:
            block_hash = block.hash
            total_participated_deposits = block_vote_cache[block_hash]['total_voter_deposits']
            voter_indices = block_vote_cache[block_hash]['total_voter_deposits']
        else:
            total_participated_deposits = 0
            voter_indices = set()

        participating_validator_indices = filter(
            lambda index: index in voter_indices,
            active_validator_indices
        )
        non_participating_validator_indices = filter(
            lambda index: index not in voter_indices,
            active_validator_indices
        )
        # finalized recently?
        if time_since_finality <= 2 * config['cycle_length']:
            for index in participating_validator_indices:
                rewards_and_penalties[index] += (
                    validators[index].balance //
                    reward_quotient *
                    (2 * total_participated_deposits - total_deposits) //
                    total_deposits
                )
            for index in non_participating_validator_indices:
                rewards_and_penalties[index] -= (
                    validators[index].balance //
                    reward_quotient
                )
        else:
            for index in non_participating_validator_indices:
                rewards_and_penalties[index] = (
                    validators[index].balance //
                    reward_quotient +
                    validators[index].balance *
                    time_since_finality //
                    quadratic_penalty_quotient
                )

    return rewards_and_penalties


def calculate_crosslink_rewards(crystallized_state: CrystallizedState,
                                active_state: ActiveState,
                                block: 'Block',
                                config: Dict[str, Any]=DEFAULT_CONFIG) -> List[int]:
    validators = crystallized_state.validators
    rewards_and_penalties = [0 for _ in validators]  # type: List[int]

    #
    # STUB
    # Still need clarity in spec to properly fill these calculations
    #

    return rewards_and_penalties


def apply_rewards_and_penalties(crystallized_state: CrystallizedState,
                                active_state: ActiveState,
                                block: 'Block',
                                config: Dict[str, Any]=DEFAULT_CONFIG) -> List['ValidatorRecord']:
    # FFG Rewards
    ffg_rewards = calculate_ffg_rewards(
        crystallized_state,
        active_state,
        block,
        config=config
    )

    # Crosslink Rewards
    crosslink_rewards = calculate_crosslink_rewards(
        crystallized_state,
        active_state,
        block,
        config=config
    )

    updated_validators = deepcopy(crystallized_state.validators)
    active_validator_indices = get_active_validator_indices(
        crystallized_state.current_dynasty,
        crystallized_state.validators
    )

    # apply rewards and penalties
    for index in active_validator_indices:
        updated_validators[index].balance += (
            ffg_rewards[index] +
            crosslink_rewards[index]
        )

    return updated_validators


def ready_for_dynasty_transition(crystallized_state: CrystallizedState,
                                 block: 'Block',
                                 config: Dict[str, Any]=DEFAULT_CONFIG) -> bool:
    slots_since_last_dynasty_change = block.slot_number - crystallized_state.dynasty_start
    if slots_since_last_dynasty_change < config['min_dynasty_length']:
        return False

    if crystallized_state.last_finalized_slot <= crystallized_state.dynasty_start:
        return False

    # gather every shard in shard_and_committee_for_slots
    required_shards = set()
    for shard_and_committee_for_slot in crystallized_state.shard_and_committee_for_slots:
        for shard_and_committee in shard_and_committee_for_slot:
            required_shards.add(shard_and_committee.shard_id)

    # check that crosslinks were updated for all required shards
    for shard_id, crosslink in enumerate(crystallized_state.crosslink_records):
        if shard_id in required_shards:
            if crosslink.slot <= crystallized_state.dynasty_start:
                return False

    return True


def compute_dynasty_transition(crystallized_state: CrystallizedState,
                               block: 'Block',
                               config: Dict[str, Any]=DEFAULT_CONFIG) -> CrystallizedState:
    crystallized_state = deepcopy(crystallized_state)
    crystallized_state.current_dynasty += 1

    # Not current in spec, but should be added soon
    crystallized_state.dynasty_start = crystallized_state.last_state_recalc

    next_start_shard = (
        (crystallized_state.shard_and_committee_for_slots[-1][-1].shard_id + 1) %
        config['shard_count']
    )

    crystallized_state.shard_and_committee_for_slots[config['cycle_length']:] = get_new_shuffling(
        block.parent_hash,  # stub until better RNG
        crystallized_state.validators,
        crystallized_state.current_dynasty,
        next_start_shard
    )

    return crystallized_state


def compute_cycle_transitions(
        crystallized_state: CrystallizedState,
        active_state: ActiveState,
        block: 'Block',
        config: Dict[str, Any]=DEFAULT_CONFIG) -> Tuple[CrystallizedState, ActiveState]:
    while block.slot_number >= crystallized_state.last_state_recalc + config['cycle_length']:
        crystallized_state, active_state = initialize_new_cycle(
            crystallized_state,
            active_state,
            block,
            config=config
        )

        if ready_for_dynasty_transition(crystallized_state, block, config):
            crystallized_state = compute_dynasty_transition(
                crystallized_state,
                block,
                config=config
            )

    return crystallized_state, active_state


def compute_state_transition(
        parent_state: Tuple[CrystallizedState, ActiveState],
        parent_block: 'Block',
        block: 'Block',
        config: Dict[str, Any]=DEFAULT_CONFIG) -> Tuple[CrystallizedState, ActiveState]:
    crystallized_state, active_state = parent_state

    validate_block_pre_processing_conditions(
        block,
        parent_block,
        crystallized_state,
        config=config,
    )

    # Update active state to fill any missing hashes with parent block hash
    active_state = fill_recent_block_hashes(active_state, parent_block, block)

    # process per block state changes
    active_state = process_block(
        crystallized_state,
        active_state,
        block,
        parent_block,
        config
    )

    # Initialize a new cycle(s) if needed
    crystallized_state, active_state = compute_cycle_transitions(
        crystallized_state,
        active_state,
        block,
        config=config,
    )

    return crystallized_state, active_state
