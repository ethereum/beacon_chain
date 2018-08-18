from .config import (
    DEFAULT_CONFIG,
)
from .active_state import (
    ActiveState,
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
    get_signed_parent_hashes,
)

import beacon_chain.utils.bls as bls
from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.utils.bitfield import (
    get_bitfield_length,
    has_voted,
)
from beacon_chain.utils.simpleserialize import (
    deepcopy,
)


def validate_block(block):
    # ensure parent processed
    # ensure pow_chain_ref processed
    # ensure local time is large enough to process this block's slot

    return True


def validate_attestation(crystallized_state,
                         active_state,
                         attestation,
                         block,
                         config=DEFAULT_CONFIG):
    if not attestation.slot < block.slot_number:
        raise Exception("Attestation slot number too high")

    if not (attestation.slot > block.slot_number - config['cycle_length']):
        raise Exception(
            "Attestation slot number too low:\n"
            "\tFound: %s, Needed greater than: %s" %
            (attestation.slot, block.slot_number - config['cycle_length'])
        )

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
    in_cycle_slot_height = attestation.slot % config['cycle_length']
    pub_keys = [
        crystallized_state.validators[index].pubkey
        for i, index in enumerate(attestation_indices)
        if has_voted(attestation.attester_bitfield, i)
    ]
    message = blake(
        in_cycle_slot_height.to_bytes(8, byteorder='big') +
        b''.join(parent_hashes) +
        attestation.shard_id.to_bytes(2, byteorder='big') +
        attestation.shard_block_hash
    )
    if not bls.verify(message, bls.aggregate_pubs(pub_keys), attestation.aggregate_sig):
        raise Exception("Attestation aggregate signature fails")


def get_updated_block_vote_cache(crystallized_state,
                                 active_state,
                                 attestation,
                                 block,
                                 block_vote_cache,
                                 config):
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
                new_block_vote_cache[parent_hash]['total_voter_deposits'] += crystallized_state.validators[index].balance

    return new_block_vote_cache


def process_block(crystallized_state,
                   active_state,
                   block,
                   config=DEFAULT_CONFIG):
    new_block_vote_cache = deepcopy(active_state.block_vote_cache)
    for attestation in block.attestations:
        validate_attestation(crystallized_state,
                             active_state,
                             attestation,
                             block,
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

    new_active_state = ActiveState(
        pending_attestations=new_attestations,
        recent_block_hashes=active_state.recent_block_hashes[:],
        block_vote_cache=new_block_vote_cache
    )
    return new_active_state


def process_updated_crosslinks(crystallized_state,
                               active_state,
                               config=DEFAULT_CONFIG):
    total_attestation_balance = {}
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
                hash=attestation.shard_block_hash
            )
    return crosslinks


def initialize_new_cycle(crystallized_state,
                         active_state,
                         block,
                         config=DEFAULT_CONFIG):
    cycle_length = config['cycle_length']
    last_state_recalc = crystallized_state.last_state_recalc
    last_justified_slot = crystallized_state.last_justified_slot
    last_finalized_slot = crystallized_state.last_finalized_slot
    justified_streak = crystallized_state.justified_streak
    # walk through slots last_state_recalc - CYCLE_LENGTH ... last_state_recalc - 1
    # and check for justification, streaks, and finality
    for i in range(cycle_length):
        slot = i + (last_state_recalc - cycle_length)

        block_hash = active_state.recent_block_hashes[i]
        if block_hash in active_state.block_vote_cache:
            vote_balance = active_state.block_vote_cache[block_hash]['total_voter_deposits']
        else:
            vote_balance = 0

        if 3 * vote_balance >= 2 * crystallized_state.total_deposits:
            last_justified_slot = max(last_justified_slot, slot)
            justified_streak += 1
        else:
            justified_streak = 0

        if justified_streak >= cycle_length + 1:
            last_finalized_slot = max(last_finalized_slot, slot - cycle_length - 1)

    crosslink_records = process_updated_crosslinks(
        crystallized_state,
        active_state,
        config
    )

    # remove attestations older than last_state_recalc
    pending_attestations = [
        a for a in active_state.pending_attestations
        if a.slot >= last_state_recalc
    ]

    dynasty = crystallized_state.current_dynasty  # STUB
    dynasty_seed = crystallized_state.dynasty_seed  # STUB
    dynasty_seed_last_reset = crystallized_state.dynasty_seed_last_reset  # STUB
    crosslinking_start_shard = 0  # stub. Needs to see where this epoch left off
    validators = deepcopy(crystallized_state.validators)  # STUB
    indices_for_heights = (
        crystallized_state.indices_for_heights[cycle_length:] +
        # this is a stub and will be addressed by shuffling at dynasty change
        crystallized_state.indices_for_heights[cycle_length:]
    )
    active_validator_indices = get_active_validator_indices(dynasty, validators)

    new_crystallized_state = CrystallizedState(
        validators=validators,
        last_state_recalc=last_state_recalc + cycle_length,
        indices_for_heights=indices_for_heights,
        last_justified_slot=last_justified_slot,
        justified_streak=justified_streak,
        last_finalized_slot=last_finalized_slot,
        current_dynasty=crystallized_state.current_dynasty,
        crosslinking_start_shard=crosslinking_start_shard,
        crosslink_records=crosslink_records,
        total_deposits=sum(map(lambda i: validators[i].balance, active_validator_indices)),
        dynasty_seed=dynasty_seed,
        dynasty_seed_last_reset=dynasty_seed_last_reset
    )

    new_active_state = ActiveState(
        pending_attestations=pending_attestations,
        recent_block_hashes=active_state.recent_block_hashes[:],
        # Should probably clean up block_vote_cache but old records won't break cache
        # so okay for now
        block_vote_cache=deepcopy(active_state.block_vote_cache)
    )

    return new_crystallized_state, new_active_state


def fill_recent_block_hashes(active_state,
                             parent_block,
                             block):
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


def compute_state_transition(parent_state,
                             parent_block,
                             block,
                             config=DEFAULT_CONFIG):
    crystallized_state, active_state = parent_state

    assert validate_block(block)

    # Update active state to fill any missing hashes with parent block hash
    active_state = fill_recent_block_hashes(active_state, parent_block, block)

    # Initialize a new cycle if needed
    if block.slot_number >= (crystallized_state.last_state_recalc + config['cycle_length']):
        crystallized_state, active_state = initialize_new_cycle(
            crystallized_state,
            active_state,
            block,
            config
        )

    # process per block state changes
    active_state = process_block(
        crystallized_state,
        active_state,
        block,
        config
    )

    return crystallized_state, active_state
