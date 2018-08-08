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
    # NOTE: This is spec'd incorrectly and will likely change pending review from  Vitalik
    parent_hashes = (
        attestation.oblique_parent_hashes +
        active_state.recent_block_hashes[
            block.slot_number - attestation.slot + len(attestation.oblique_parent_hashes):
        ]
    )
    return parent_hashes


def get_attestation_indices(crystallized_state,
                            block,
                            attestation,
                            config=DEFAULT_CONFIG):
    last_epoch_start = (crystallized_state.epoch_number - 1) * config['epoch_length']

    shard_position = filter(
        lambda x: crystallized_state.indices_for_heights[block.slot - last_epoch_start][x].shard_id == attestation.shard_id,
        range(len(crystallized_state.indices_for_heights[block.slot - last_epoch_start]))
    )[0]
    attestation_indices = crystallized_state.indices_for_heights[block.slot - last_epoch_start][shard_position].shard_id

    return attestation_indices


def validate_attestation(crystallized_state,
                         active_state,
                         attestation,
                         block,
                         config=DEFAULT_CONFIG):
    if not attestation.slot < block.slot_number:
        print("Attestation slot number too high")
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
        crystallized_state.validators[i].pubkey
        for i in attestation_indices
        if has_voted(attestation.attester_bitfield, i)
    ]
    message = blake(
        in_epoch_slot_height.to_bytes(8, byteorder='big') +
        parent_hashes +
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
        new_block_vote_cache = _update_block_vote_cache(crystallized_state,
                                                        active_state,
                                                        attestation,
                                                        block,
                                                        new_block_vote_cache,
                                                        config)

    new_attestations = active_state.pending_attestations + block.attestations,
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
                          block,
                          config=DEFAULT_CONFIG):
    new_active_validators = deepcopy(crystallized_state.active_validators)
    attester_bitfield = active_state.attester_bitfield

    #
    # Justify and Finalize
    #
    justify = active_state.total_attester_deposits * 3 >= crystallized_state.total_deposits * 2
    finalize = (
        justify and
        crystallized_state.last_justified_epoch == crystallized_state.current_epoch - 1
    )
    if justify:
        last_justified_epoch = crystallized_state.current_epoch
    else:
        last_justified_epoch = crystallized_state.last_justified_epoch

    if finalize:
        last_finalized_epoch = crystallized_state.last_justified_epoch
    else:
        last_finalized_epoch = crystallized_state.last_finalized_epoch

    #
    # Compute and apply FFG rewards/penalties
    #
    online_reward, offline_penalty = _compute_ffg_participation_rewards(
        crystallized_state,
        active_state,
        config
    )

    for index in range(crystallized_state.num_active_validators):
        validator = new_active_validators[
            crystallized_state.current_shuffling[index]
        ]
        if has_voted(attester_bitfield, index):
            validator.balance += online_reward
        else:
            validator.balance -= offline_penalty

    #
    # Process crosslink roots and rewards
    #
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

    #
    # reshuffling
    #
    epochs_since_seed_reset = crystallized_state.current_epoch - crystallized_state.dynasty_seed_last_reset
    if is_power_of_two(epochs_since_seed_reset):
        temp_seed = blake(
            crystallized_state.dynasty_seed +
            bytes(int(log(epochs_since_seed_reset, 2)))
        )

        new_current_shuffling = get_shuffling(temp_seed, len(new_active_validators))
    else:
        new_current_shuffling = crystallized_state.current_shuffling

    #
    # STUB: perform dynasty transition
    #
    if finalize:
        new_current_dynasty = crystallized_state.current_dynasty + 1
        # STUB until real RNG
        new_dynasty_seed = blake(crystallized_state.dynasty_seed)
        new_dynasty_seed_last_reset = crystallized_state.current_epoch
    else:
        new_current_dynasty = crystallized_state.current_dynasty
        new_dynasty_seed = crystallized_state.dynasty_seed
        new_dynasty_seed_last_reset = crystallized_state.dynasty_seed_last_reset

    #
    # Generate and return updated state
    #
    new_crystallized_state = CrystallizedState(
        # do not currently handle validator rotation
        active_validators=new_active_validators,
        queued_validators=crystallized_state.new_queued_validators,
        exited_validators=crystallized_state.new_exited_validators,
        current_epoch=crystallized_state.current_epoch + 1,
        current_shuffling=new_current_shuffling,
        last_justified_epoch=last_justified_epoch,
        last_finalized_epoch=last_finalized_epoch,
        current_dynasty=new_current_dynasty,
        next_shard=crystallized_state.next_shard,  # STUB
        current_checkpoint=block.parent_hash,
        crosslink_records=new_crosslink_records,
        total_deposits=sum(map(lambda v: v.balance, new_active_validators)),
        dynasty_seed=new_dynasty_seed,
        dynasty_seed_last_reset=new_dynasty_seed_last_reset
    )

    new_active_state = ActiveState(
        attestations=[],
        total_attester_deposits=0,
        attester_bitfield=get_empty_bitfield(new_crystallized_state.num_active_validators)
    )

    return new_crystallized_state, new_active_state


def _initialize_new_epoch(crystallized_state,
                          active_state,
                          block,
                          config=DEFAULT_CONFIG):
    epoch_length = config['epoch_length']
    epoch_number = crystallized_state.epoch_number
    last_justified_slot = crystallized_state.last_justified_slot
    last_finalized_slot = crystallized_state.last_finalized_slot
    justified_streak = crystallized_state.justified_streak
    for i in range(epoch_length):
        slot = i + (epoch_number - 2) * epoch_length
        block_hash = crystallized_state.recent_block_hashes[i]  # assuming we store EPOCH_LENGTH * 2 block hashes
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

    indices_for_heights = crystallized_state.indices_for_heights[epoch_length:] + get_new_shuffling()  # STUB

    new_crystallized_state = CrystallizedState(
        validators=deepcopy(crystallized_state.validators),
        epoch_number=epoch_number + 1,
        indices_for_heights=indices_for_heights,
        last_justified_slot=last_justified_slot,
        justified_streak=justified_streak,
        last_finalized_slot=last_finalized_slot,
        current_dynasty=crystallized_state.current_dynasty
    )

    new_active_state = ActiveState(
        pending_attestations=pending_attestations,
        recent_block_hashes=deepcopy(active_state.recent_block_hashes),
        # Should probably clean up block_vote_cache but old records won't break cache
        # so okay for now
        block_vote_cache=copy(active_state.block_vote_cache)
    )

    return new_crystallized_state, new_active_state


def compute_state_transition(parent_state,
                             block,
                             config=DEFAULT_CONFIG):
    crystallized_state, active_state = parent_state

    assert validate_block(block)


    # Initialize a new epoch if needed
    if block.slot_number >= (crystallized_state.epoch_number + 1) * config['epoch_length']:
        crystallized_state, active_state = _initialize_new_epoch(
            crystallized_state,
            active_state,
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
