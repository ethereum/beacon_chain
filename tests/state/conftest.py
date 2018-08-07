import pytest
import random

from beacon_chain.state.config import (
    DEFAULT_SWITCH_DYNASTY,
    DEPOSIT_SIZE,
    END_EPOCH_GRACE_PERIOD,
    EPOCH_LENGTH,
    MAX_VALIDATOR_COUNT,
    MIN_COMMITTEE_SIZE,
    SHARD_COUNT,
    SLOT_DURATION,
    generate_config,
)
from beacon_chain.state.active_state import (
    ActiveState,
)
from beacon_chain.state.attestation_record import (
    AttestationRecord,
)
from beacon_chain.state.aggregate_vote import (
    AggregateVote,
)
from beacon_chain.state.block import (
    Block,
)
from beacon_chain.state.crosslink_record import (
    CrosslinkRecord,
)
from beacon_chain.state.crystallized_state import (
    CrystallizedState,
)
from beacon_chain.state.validator_record import (
    ValidatorRecord,
)
from beacon_chain.state.new_state_transition import (
    compute_state_transition,
)
from beacon_chain.state.helpers import (
    get_cutoffs,
    get_si_for_height,
    get_shuffling,
    get_crosslink_shards,
    get_crosslink_notaries,
)


import beacon_chain.utils.bls
from beacon_chain.utils.bitfield import (
    get_empty_bitfield,
    set_voted,
)
from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.utils.simpleserialize import (
    serialize,
)

bls = beacon_chain.utils.bls

DEFAULT_SHUFFLING_SEED = b'\35'*32
DEFAULT_RANDAO = b'\45'*32
DEFAULT_NUM_VALIDATORS = 40


def bls_verify_mock(m, pub, sig):
    return True


def bls_sign_mock(m, k):
    return 0, 0


@pytest.fixture(autouse=True)
def mock_bls(mocker):
    mocker.patch('beacon_chain.utils.bls.verify', side_effect=bls_verify_mock)
    mocker.patch('beacon_chain.utils.bls.sign', side_effect=bls_sign_mock)


@pytest.fixture
def sample_active_state_params():
    return {
        'pending_attestations': [],
        'recent_block_hashes': [],
    }


@pytest.fixture
def sample_attestation_record_params():
    return {
        'slot': 10,
        'parent_hash': b'\x34'*32,
        'checkpoint_hash': b'\x42'*32,
        'shard_id': 12,
        'shard_block_hash': b'\x20'*32,
        'attester_bitfield': b'\x33\x1F',
        'aggregate_sig': [0, 0],
    }


@pytest.fixture
def sample_crystallized_state_params():
    return {
        'validators': [],
        'epoch_number': 30,
        'indices_for_heights': [],
        'last_justified_slot': 100,
        'justified_streak': 10,
        'last_finalized_slot': 70,
        'current_dynasty': 4,
        'crosslinking_start_shard': 2,
        'current_checkpoint': b'\x43'*32,
        'crosslink_records': [],
        'total_deposits': 10000,
        'dynasty_seed': b'\x55'*32,
        'dynasty_seed_last_reset': 3,
    }


@pytest.fixture
def sample_recent_proposer_record_params():
    return {
        'index': 10,
        'randao_commitment': b'\x43'*32,
        'balance_delta': 3
    }


@pytest.fixture
def sample_shard_and_indices_params():
    return {
        'shard_id': 10,
        'validators': [],
    }


@pytest.fixture
def sample_crosslink_record_params():
    return {
        'epoch': 0,
        'hash': b'\x43'*32,
    }


@pytest.fixture
def init_shuffling_seed():
    return DEFAULT_SHUFFLING_SEED


@pytest.fixture
def init_randao():
    return DEFAULT_RANDAO


@pytest.fixture
def default_switch_dynasty():
    return DEFAULT_SWITCH_DYNASTY


@pytest.fixture
def deposit_size():
    return DEPOSIT_SIZE


@pytest.fixture
def end_epoch_grace_period():
    return END_EPOCH_GRACE_PERIOD


@pytest.fixture
def epoch_length():
    return EPOCH_LENGTH


@pytest.fixture
def max_validator_count():
    return MAX_VALIDATOR_COUNT


@pytest.fixture
def min_committee_size():
    return MIN_COMMITTEE_SIZE


@pytest.fixture
def shard_count():
    return SHARD_COUNT


@pytest.fixture
def slot_duration():
    return SLOT_DURATION


@pytest.fixture
def config(default_switch_dynasty,
           deposit_size,
           end_epoch_grace_period,
           epoch_length,
           max_validator_count,
           min_committee_size,
           shard_count,
           slot_duration):
    return generate_config(
        default_switch_dynasty=default_switch_dynasty,
        deposit_size=deposit_size,
        end_epoch_grace_period=end_epoch_grace_period,
        epoch_length=epoch_length,
        max_validator_count=max_validator_count,
        min_committee_size=min_committee_size,
        shard_count=shard_count,
        slot_duration=slot_duration
    )


@pytest.fixture
def num_validators():
    return DEFAULT_NUM_VALIDATORS


@pytest.fixture
def init_validator_keys(pubkeys, num_validators):
    return pubkeys[:num_validators]


@pytest.fixture
def genesis_crystallized_state(init_validator_keys,
                               init_shuffling_seed,
                               config):
    return CrystallizedState(
        active_validators=[ValidatorRecord(
            pubkey=pub,
            withdrawal_shard=0,
            withdrawal_address=blake(pub.to_bytes(32, 'big'))[-20:],
            randao_commitment=b'\x55'*32,
            balance=config['deposit_size'],
            switch_dynasty=config['default_switch_dynasty']
        ) for pub in init_validator_keys],
        queued_validators=[],
        exited_validators=[],
        current_epoch=1,
        current_shuffling=get_shuffling(
            init_shuffling_seed,
            len(init_validator_keys),
            config=config
        ),
        last_justified_epoch=0,
        last_finalized_epoch=0,
        current_dynasty=1,
        next_shard=0,
        current_checkpoint=blake(b'insert EOS constitution here'),
        crosslink_records=[
            CrosslinkRecord(hash=b'\x00'*32, epoch=0) for i in range(SHARD_COUNT)
        ],
        total_deposits=config['deposit_size']*len(init_validator_keys),
        dynasty_seed=init_shuffling_seed,
        dynasty_seed_last_reset=1
    )


@pytest.fixture
def genesis_active_state(genesis_crystallized_state):
    return ActiveState(
        attestations=[],
        total_attester_deposits=0,
        attester_bitfield=get_empty_bitfield(genesis_crystallized_state.num_active_validators)
    )


@pytest.fixture
def genesis_block(genesis_crystallized_state, genesis_active_state):
    return Block(
        parent_hash=b'\x00'*32,
        slot_number=0,
        randao_reveal=b'\x00'*32,
        attestations=[],
        pow_chain_ref=b'\x00'*32,
        active_state_root=b'\x00'*32,
        crystallized_state_root=b'\x00'*32,
    )


# NOT FIXED
# Mock makes a block based upon the params passed indices
@pytest.fixture
def make_unfinished_block(keymap, config):
    def make_unfinished_block(parent_state,
                              parent,
                              skips,
                              attester_share=0.8,
                              crosslink_shards_and_shares=None):
        if crosslink_shards_and_shares is None:
            crosslink_shards_and_shares = []

        crystallized_state, active_state = parent_state
        parent_attestation = serialize(parent)
        indices, proposer = get_attesters_and_proposer(
            crystallized_state,
            active_state,
            skips,
            config
        )

        print('Selected indices: %r' % indices)
        print('Selected block proposer: %d' % proposer)

        # Randomly pick indices to include
        is_attesting = [random.random() < attester_share for _ in indices]
        # Attestations
        sigs = [
            bls.sign(
                parent_attestation,
                keymap[crystallized_state.active_validators[indices[i]].pubkey]
            )
            for i, attesting in enumerate(is_attesting) if attesting
        ]
        attestation_aggregate_sig = bls.aggregate_sigs(sigs)
        print('Aggregated sig')

        attestation_bitfield = get_empty_bitfield(len(indices))
        for i, attesting in enumerate(is_attesting):
            if attesting:
                attestation_bitfield = set_voted(attestation_bitfield, i)
        print('Aggregate bitfield:', bin(int.from_bytes(attestation_bitfield, 'big')))

        # Randomly pick indices to include for crosslinks
        shard_aggregate_votes = []

        # The shards that are selected to be crosslinking
        crosslink_shards = get_crosslink_shards(crystallized_state, config=config)

        for shard, crosslinker_share in crosslink_shards_and_shares:
            # Check if this shard is in the crosslink shards list
            assert shard in crosslink_shards

            print('Making crosslink in shard %d' % shard)
            indices = get_crosslink_notaries(crystallized_state, shard, crosslink_shards=crosslink_shards, config=config)
            print('Indices: %r' % indices)
            is_notarizing = [random.random() < attester_share for _ in indices]
            notary_bitfield = get_empty_bitfield(len(indices))
            for i, notarizing in enumerate(is_notarizing):
                if notarizing:
                    notary_bitfield = set_voted(notary_bitfield, i)
            print('Bitfield:', bin(int.from_bytes(notary_bitfield, 'big')))
            shard_block_hash = blake(bytes([shard]))
            crosslink_attestation_hash = get_crosslink_aggvote_msg(
                shard,
                shard_block_hash,
                crystallized_state
            )
            sigs = [
                bls.sign(
                    crosslink_attestation_hash,
                    keymap[crystallized_state.active_validators[indices[i]].pubkey]
                )
                for i, notarizing in enumerate(is_notarizing) if notarizing
            ]
            v = AggregateVote(
                shard_id=shard,
                shard_block_hash=shard_block_hash,
                notary_bitfield=notary_bitfield,
                aggregate_sig=list(bls.aggregate_sigs(sigs))
            )
            shard_aggregate_votes.append(v)
        print('Added %d shard aggregate votes' % len(crosslink_shards_and_shares))

        block = Block(
            parent_hash=blake(parent_attestation),
            skip_count=skips,
            randao_reveal=blake(str(random.random()).encode('utf-8')),
            attestation_bitfield=attestation_bitfield,
            attestation_aggregate_sig=list(attestation_aggregate_sig),
            shard_aggregate_votes=shard_aggregate_votes,
            main_chain_ref=b'\x00'*32,
            state_hash=b'\x00'*64
        )
        return block, proposer
    return make_unfinished_block


@pytest.fixture
def mock_make_attestations(keymap, config):
    def mock_make_attestations(parent_state,
                               block,
                               attester_share=0.8):
        print(config)
        crystallized_state, active_state = parent_state

        height_cutoffs, shard_cutoffs = get_cutoffs(
            crystallized_state.num_active_validators,
            config
        )
        in_epoch_slot_height = block.slot_number % config['epoch_length']

        sis = get_si_for_height(
            height_cutoffs,
            shard_cutoffs,
            in_epoch_slot_height,
            config
        )
        print("Generating attestations for shards: %s" % sis)

        attestations = []
        for si in sis:
            if in_epoch_slot_height < config['epoch_length'] - config['end_epoch_grace_period']:
                start = shard_cutoffs[si]
                end = shard_cutoffs[si + 1]
            else:
                start = height_cutoffs[in_epoch_slot_height]
                end = height_cutoffs[in_epoch_slot_height]

            # reverse
            shard_id = (si + crystallized_state.next_shard) % config['shard_count']
            print("Generating attestation for shard %s" % shard_id)

            # Create attestation
            attestation = AttestationRecord(
                slot=block.slot_number,
                parent_hash=blake(serialize(block)),
                checkpoint_hash=crystallized_state.current_checkpoint,
                shard_id=shard_id,
                shard_block_hash=blake(bytes(str(shard_id), 'utf-8')),
                attester_bitfield=get_empty_bitfield(end - start)
            )

            # Randomly pick indices to include
            is_attesting = [random.random() < attester_share for _ in range(end - start)]
            # Proposer always attests
            is_attesting[0] = True

            # Sign with is_attesting and set bit field
            # THE FOLLOWING IS WRONG
            message = blake(
                in_epoch_slot_height.to_bytes(8, byteorder='big') +
                attestation.parent_hash +
                attestation.checkpoint_hash +
                attestation.shard_id.to_bytes(2, byteorder='big') +
                attestation.shard_block_hash
            )
            sigs = [
                bls.sign(
                    message,
                    keymap[
                        crystallized_state.active_validators[
                            crystallized_state.current_shuffling[start + i]
                        ].pubkey
                    ]
                )
                for i, attesting in enumerate(is_attesting) if attesting
            ]
            attestation.aggregate_sig = bls.aggregate_sigs(sigs)
            print('Aggregated sig')

            attestation_bitfield = get_empty_bitfield(end - start)
            for i, attesting in enumerate(is_attesting):
                if attesting:
                    attestation_bitfield = set_voted(attestation_bitfield, i)
            attestation.attester_bitfield = attestation_bitfield
            print('Aggregate bitfield:', bin(int.from_bytes(attestation_bitfield, 'big')))

            attestations.append(attestation)

        # TODO include blank attestations for the end period
        # find start and end of validators in current shuffling
        # if in_epoch_slot_height < config['epoch_length'] - config['end_epoch_grace_period']:
            # si = (attestation.shard_id - crystallized_state.next_shard) % config['shard_count']
            # start = shard_cutoffs[si]
            # end = shard_cutoffs[si + 1]
        # else:
            # start = height_cutoffs[in_epoch_slot_height]
            # end = height_cutoffs[in_epoch_slot_height]

        return attestations
    return mock_make_attestations

 
@pytest.fixture
def mock_make_child(keymap, make_unfinished_block, config):
    def mock_make_child(parent_state,
                        parent,
                        slot_number,
                        attestations=None):
        if attestations is None:
            attestations = []

        crystallized_state, active_state = parent_state
        block = Block(
            parent_hash=blake(serialize(parent)),
            slot_number=slot_number,
            randao_reveal=blake(str(random.random()).encode('utf-8')),
            attestations=attestations,
            pow_chain_ref=b'\x00'*32,
            active_state_root=b'\x00'*32,
            crystallized_state_root=b'\x00'*32
        )
        print('Generated preliminary block header')

        new_crystallized_state, new_active_state = compute_state_transition(
            (crystallized_state, active_state),
            block,
            config=config
        )
        print('Calculated state transition')

        if crystallized_state == new_crystallized_state:
            block.crystallized_state_root = parent.crystallized_state_root
        else:
            block.crystallized_state_root = blake(serialize(crystallized_state))

        block.active_state_root = blake(serialize(active_state))

        return block, new_crystallized_state, new_active_state
    return mock_make_child
