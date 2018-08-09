from copy import copy
from math import log

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
    get_new_shuffling,
)

import beacon_chain.utils.bls as bls
from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.utils.bitfield import (
    get_bitfield_length,
    get_empty_bitfield,
    has_voted,
    or_bitfields,
    set_voted,
)
from beacon_chain.utils.simpleserialize import (
    deepcopy,
)


def is_power_of_two(num):
    return ((num & (num - 1)) == 0) and num != 0


def _compute_ffg_participation_rewards(crystallized_state,
                                       active_state,
                                       config):
    # STUB
    return 1, 1


def validate_block(block):
    # ensure parent processed
    # ensure pow_chain_ref processed
    # ensure local time is large enough to process this block's slot

    return True


def get_parent_hashes(active_state,
                      block,
                      attestation,
                      config=DEFAULT_CONFIG):
    epoch_length = config['epoch_length']
    oblique_parent_hashes = attestation.oblique_parent_hashes

    parent_hashes = (
        active_state.recent_block_hashes[
            epoch_length + attestation.slot - block.slot_number:
            epoch_length * 2 + attestation.slot - block.slot_number - len(oblique_parent_hashes)
        ] +
        oblique_parent_hashes

    )
    return parent_hashes


def get_attestation_indices(crystallized_state,
                            block,
                            attestation,
                            config=DEFAULT_CONFIG):
    last_epoch_start = (crystallized_state.epoch_number - 1) * config['epoch_length']

    shard_position = list(filter(
        lambda x: crystallized_state.indices_for_heights[attestation.slot - last_epoch_start][x].shard_id == attestation.shard_id,
        range(len(crystallized_state.indices_for_heights[attestation.slot - last_epoch_start]))
    ))[0]
    attestation_indices = crystallized_state.indices_for_heights[attestation.slot - last_epoch_start][shard_position].committee

    return attestation_indices


def validate_attestation(crystallized_state,
                         active_state,
                         attestation,
                         block,
                         config=DEFAULT_CONFIG):
    if not attestation.slot < block.slot_number:
        print("Attestation slot number too high")
        return False

    if not (attestation.slot > block.slot_number - config['epoch_length']):
        print("Attestation slot number too low:")
        print(
            "\tFound: %s, Needed greater than: %s" %
            (attestation.slot, block.slot_number - config['epoch_length'])
        )
        return False

    parent_hashes = get_parent_hashes(
        active_state,
        block,
        attestation,
        config
    )
    attestation_indices = get_attestation_indices(
        crystallized_state,
        block,
        attestation,
        config
    )

    #
    # validate bitfield
    #
    if not (len(attestation.attester_bitfield) == get_bitfield_length(len(attestation_indices))):
        print(
            "Attestation has incorrect bitfield length. Found: %s, Expected: %s" %
            (len(attestation.attester_bitfield), get_bitfield_length(len(attestation_indices)))
        )
        return False

    # check if end bits are zero
    last_bit = len(attestation_indices)
    if last_bit % 8 != 0:
        for i in range(8 - last_bit % 8):
            if has_voted(attestation.attester_bitfield, last_bit + i):
                print("Attestation has non-zero trailing bits")
                return False

    #
    # validate aggregate_sig
    #
    in_epoch_slot_height = attestation.slot % config['epoch_length']
    pub_keys = [
        crystallized_state.validators[index].pubkey
        for i, index in enumerate(attestation_indices)
        if has_voted(attestation.attester_bitfield, i)
    ]
    message = blake(
        in_epoch_slot_height.to_bytes(8, byteorder='big') +
        b''.join(parent_hashes) +
        attestation.shard_id.to_bytes(2, byteorder='big') +
        attestation.shard_block_hash
    )
    if not bls.verify(message, bls.aggregate_pubs(pub_keys), attestation.aggregate_sig):
        print("Attestation aggregate signature fails")
        return False

    return True


def _update_block_vote_cache(crystallized_state,
                             active_state,
                             attestation,
                             block,
                             block_vote_cache,
                             config):
    new_block_vote_cache = copy(block_vote_cache)
    parent_hashes = get_parent_hashes(
        active_state,
        block,
        attestation,
        config
    )
    attestation_indices = get_attestation_indices(
        crystallized_state,
        block,
        attestation,
        config
    )

    for parent_hash in parent_hashes:
        if parent_hash in attestation.oblique_parent_hashes:
            continue
        if parent_hash not in new_block_vote_cache:
            new_block_vote_cache = {
                'voter_indices': set(),
                'total_voter_deposits': 0
            }
        for i in attestation_indices:
            if i not in new_block_vote_cache['voter_indices']:
                new_block_vote_cache['voter_indices'].add(i)
                new_block_vote_cache['total_voter_deposits'] += crystallized_state.validators[i].balance

    return new_block_vote_cache


def _process_block(crystallized_state,
                   active_state,
                   block,
                   config=DEFAULT_CONFIG):
    new_block_vote_cache = copy(active_state.block_vote_cache)
    for attestation in block.attestations:
        assert validate_attestation(crystallized_state,
                                    active_state,
                                    attestation,
                                    block,
                                    config)
        new_block_vote_cache = _update_block_vote_cache(
            crystallized_state,
            active_state,
            attestation,
            block,
            new_block_vote_cache,
            config
        )

    new_attestations = active_state.pending_attestations + block.attestations
    new_recent_block_hashes = (
        active_state.recent_block_hashes[1:] +
        [block.hash]
    )

    new_active_state = ActiveState(
        pending_attestations=new_attestations,
        recent_block_hashes=new_recent_block_hashes,
        block_vote_cache=new_block_vote_cache
    )
    return new_active_state


def _initialize_new_epoch(crystallized_state,
                          active_state,
                          parent_block,
                          block,
                          config=DEFAULT_CONFIG):
    epoch_length = config['epoch_length']
    epoch_number = crystallized_state.epoch_number
    last_justified_slot = crystallized_state.last_justified_slot
    last_finalized_slot = crystallized_state.last_finalized_slot
    justified_streak = crystallized_state.justified_streak
    for i in range(epoch_length):
        slot = i + (epoch_number - 2) * epoch_length
        # next line assuming we store EPOCH_LENGTH * 2 block hashes
        block_hash = active_state.recent_block_hashes[i]
        if block_hash in active_state.block_vote_cache:
            vote_balance = active_state.block_vote_cache[block_hash]['total_voter_deposits']
        else:
            vote_balance = 0

        # need to make sure that `total_deposits` only accounts for active
        if 3 * vote_balance >= 2 * crystallized_state.total_deposits:
            last_justified_slot = max(last_justified_slot, slot)
            justified_streak += 1
        else:
            justified_streak = 0

        if justified_streak >= epoch_length + 1:
            last_finalized_slot = max(last_finalized_slot, slot)

    pending_attestations = [
        a for a in active_state.pending_attestations
        if a.slot >= (epoch_number - 1) * epoch_length
    ]

    dynasty = crystallized_state.current_dynasty  # STUB
    dynasty_seed = crystallized_state.dynasty_seed  # STUB
    dynasty_seed_last_reset = crystallized_state.dynasty_seed_last_reset  # STUB
    crosslinking_start_shard = 0  # stub. Needs to see where this epoch left off if didn't go through all
    validators = deepcopy(crystallized_state.validators)  # STUB
    indices_for_heights = (
        crystallized_state.indices_for_heights[epoch_length:] +
        get_new_shuffling(
            validators,
            dynasty,
            crosslinking_start_shard,
            dynasty_seed,
            config
        )  # NOTE: this is missing from spec. Assuming how it works for now
    )
    active_validator_indices = get_active_validator_indices(dynasty, validators)

    new_crystallized_state = CrystallizedState(
        validators=validators,
        epoch_number=epoch_number + 1,
        indices_for_heights=indices_for_heights,
        last_justified_slot=last_justified_slot,
        justified_streak=justified_streak,
        last_finalized_slot=last_finalized_slot,
        current_dynasty=crystallized_state.current_dynasty,
        crosslinking_start_shard=crosslinking_start_shard,
        crosslink_records=[],  # stub. current spec does not specify when crosslinks added
        total_deposits=sum(map(lambda i: validators[i].balance, active_validator_indices)),
        dynasty_seed=dynasty_seed,
        dynasty_seed_last_reset=dynasty_seed_last_reset
    )

    new_active_state = ActiveState(
        pending_attestations=pending_attestations,
        recent_block_hashes=deepcopy(active_state.recent_block_hashes),
        # Should probably clean up block_vote_cache but old records won't break cache
        # so okay for now
        block_vote_cache=copy(active_state.block_vote_cache)
    )

    return new_crystallized_state, new_active_state


def _fill_recent_block_hashes(active_state,
                              parent_block,
                              block,
                              config=DEFAULT_CONFIG):
    missing_blocks = block.slot_number - parent_block.slot_number - 1
    return ActiveState(
        pending_attestations=[a for a in active_state.pending_attestations],
        recent_block_hashes=active_state.recent_block_hashes[missing_blocks+1:] + [block.parent_hash] * missing_blocks + [block.hash],
        block_vote_cache=copy(active_state.block_vote_cache)
    )


def compute_state_transition(parent_state,
                             parent_block,
                             block,
                             config=DEFAULT_CONFIG):
    crystallized_state, active_state = parent_state

    assert validate_block(block)

    # Update active state with any missing hashes and the recent block hash
    # This is not part of the spec but is necessary to maintain proper attestation signatures
    active_state = _fill_recent_block_hashes(active_state, parent_block, block, config)


    # Initialize a new epoch if needed
    if block.slot_number >= (crystallized_state.epoch_number + 1) * config['epoch_length']:
        crystallized_state, active_state = _initialize_new_epoch(
            crystallized_state,
            active_state,
            parent_block,
            block,
            config
        )

    active_state = _process_block(
        crystallized_state,
        active_state,
        block,
        config
    )

    return crystallized_state, active_state
