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
    get_cutoffs,
    get_shuffling,
)

import beacon_chain.utils.bls as bls
from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.utils.bitfields import (
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


def validate_attestation(crystallized_state,
                         attestation,
                         block,
                         height_cutoffs,
                         shard_cutoffs,
                         config=DEFAULT_CONFIG):
    epoch_length = config['epoch_length']

    if not attestation.slot < block.slot_number:
        return False

    if not attestation.checkpoint_hash == crystallized_state.current_checkpoint:
        return False

    #
    # check valid shard and find start/end of signers
    #
    in_epoch_slot_height = attestation.slot % epoch_length
    if in_epoch_slot_height < epoch_length - config['end_epoch_grace_period']:
        si = (attestation.shard_id - crystallized_state.next_shard) % config['shard_count']

        if not (height_cutoffs[in_epoch_slot_height] <= shard_cutoffs[si] and
                shard_cutoffs[si] < height_cutoffs[in_epoch_slot_height + 1]):
            return False

        start = shard_cutoffs[si]
        end = shard_cutoffs[si + 1]
    # in grace period, no shard to attest to
    else:
        if not (attestation.shard_id == 65535 and attestation.shard_block_hash == "\x00"*32):
            return False
        start = height_cutoffs[in_epoch_slot_height]
        end = height_cutoffs[in_epoch_slot_height]

    #
    # validate bitfield
    #
    if not (len(attestation.attester_bitfield) == get_bitfield_length(end - start)):
        return False

    # check if end bits are zero
    last_bit = end - start
    if last_bit % 8 != 0:
        for i in range(8 - last_bit % 8):
            if has_voted(attestation.attester_bitfield, last_bit + i):
                return False

    #
    # validate aggregate_sig
    #
    pub_keys = [
        crystallized_state.active_validators[crystallized_state.current_shuffling[start+i]]
        for i in range(end - start)
        if has_voted(attestation.attester_bitfield, i)
    ]
    message = blake(
        in_epoch_slot_height +
        attestation.parent_hash +
        attestation.checkpoint_hash +
        attestation.shard_id +
        attestation.shard_block_hash
    )
    if not bls.verify(message, bls.aggregate_pubs(pub_keys), attestation.aggregate_sig):
        return False

    return True


def _process_attestations(crystallized_state,
                          active_state,
                          block,
                          height_cutoffs,
                          shard_cutoffs,
                          config=DEFAULT_CONFIG):

    new_attester_deposits = active_state.total_attester_deposits
    new_attester_bitfield = copy(active_state.attester_bitfield)
    for attestation in block.attestations:
        assert validate_attestation(crystallized_state,
                                    attestation,
                                    block,
                                    height_cutoffs,
                                    shard_cutoffs,
                                    config)
        in_epoch_slot_height = attestation.slot % config['epoch_length']

        # find start and end of validators in current shuffling
        if in_epoch_slot_height < config['epoch_length'] - config['end_epoch_grace_period']:
            si = (attestation.shard_id - crystallized_state.next_shard) % config['shard_count']
            start = shard_cutoffs[si]
            end = shard_cutoffs[si + 1]
        else:
            start = height_cutoffs[in_epoch_slot_height]
            end = height_cutoffs[in_epoch_slot_height]

        # mark that each validator has voted in new active state attester bitfield
        # and track total deposits voted
        for index in range(end - start):
            if not has_voted(new_attester_bitfield, index):
                validator = crystallized_state.active_validators[
                    crystallized_state.current_shuffling[start + index]
                ]
                new_attester_deposits += validator.balance
                new_attester_bitfield = set_voted(new_attester_bitfield, start + index)

    new_attestations = (
        active_state.attestations +
        sorted(block.attestations,
               key=lambda attestation: attestation.shard_block_hash)
    )

    new_active_state = ActiveState(
        attestations=new_attestations,
        total_attester_deposits=new_attester_deposits,
        attester_bitfield=new_attester_bitfield
    )
    return new_active_state


def _initialize_new_epoch(crystallized_state,
                          active_state,
                          block,
                          height_cutoffs,
                          shard_cutoffs,
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


def compute_state_transition(parent_state,
                             block,
                             config=DEFAULT_CONFIG):
    crystallized_state, active_state = parent_state

    assert validate_block(block)

    height_cutoffs, shard_cutoffs = get_cutoffs(crystallized_state.num_active_validators)

    active_state = _process_attestations(
        crystallized_state,
        active_state,
        block,
        height_cutoffs,
        shard_cutoffs,
        config
    )

    # Initialize a new epoch if needed
    if block.slot_number // config['epoch_length'] > crystallized_state.current_epoch:
        crystallized_state, active_state = _initialize_new_epoch(
            crystallized_state,
            active_state,
            block,
            height_cutoffs,
            shard_cutoffs,
            config
        )
