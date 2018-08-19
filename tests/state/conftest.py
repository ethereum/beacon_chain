import pytest
import random

from beacon_chain.state.config import (
    DEFAULT_END_DYNASTY,
    DEPOSIT_SIZE,
    CYCLE_LENGTH,
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
from beacon_chain.state.state_transition import (
    compute_state_transition,
)
from beacon_chain.state.helpers import (
    get_new_shuffling,
    get_signed_parent_hashes,
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

DEFAULT_SHUFFLING_SEED = b'\00'*32
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
        'shard_id': 12,
        'oblique_parent_hashes': [],
        'shard_block_hash': b'\x20'*32,
        'attester_bitfield': b'\x33\x1F',
        'aggregate_sig': [0, 0],
    }


@pytest.fixture
def sample_block_params():
    return {
        'parent_hash': b'\x55'*32,
        'slot_number': 10,
        'randao_reveal': b'\x34'*32,
        'attestations': [],
        'pow_chain_ref': b'\x32'*32,
        'active_state_root': b'\x01'*32,
        'crystallized_state_root': b'\x05'*32
    }


@pytest.fixture
def sample_crystallized_state_params():
    return {
        'validators': [],
        'last_state_recalc': 50,
        'indices_for_heights': [],
        'last_justified_slot': 100,
        'justified_streak': 10,
        'last_finalized_slot': 70,
        'current_dynasty': 4,
        'crosslinking_start_shard': 2,
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
def sample_shard_and_committee_params():
    return {
        'shard_id': 10,
        'committee': [],
    }


@pytest.fixture
def sample_crosslink_record_params():
    return {
        'dynasty': 2,
        'hash': b'\x43'*32,
    }


@pytest.fixture
def init_shuffling_seed():
    return DEFAULT_SHUFFLING_SEED


@pytest.fixture
def init_randao():
    return DEFAULT_RANDAO


@pytest.fixture
def default_end_dynasty():
    return DEFAULT_END_DYNASTY


@pytest.fixture
def deposit_size():
    return DEPOSIT_SIZE


@pytest.fixture
def cycle_length():
    return CYCLE_LENGTH


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
def config(default_end_dynasty,
           deposit_size,
           cycle_length,
           max_validator_count,
           min_committee_size,
           shard_count,
           slot_duration):
    return generate_config(
        default_end_dynasty=default_end_dynasty,
        deposit_size=deposit_size,
        cycle_length=cycle_length,
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
def genesis_validators(init_validator_keys,
                       config):
    current_dynasty = 1
    return [
        ValidatorRecord(
            pubkey=pub,
            withdrawal_shard=0,
            withdrawal_address=blake(pub.to_bytes(32, 'big'))[-20:],
            randao_commitment=b'\x55'*32,
            balance=config['deposit_size'],
            start_dynasty=current_dynasty,
            end_dynasty=config['default_end_dynasty']
        ) for pub in init_validator_keys
    ]


@pytest.fixture
def genesis_crystallized_state(genesis_validators,
                               init_shuffling_seed,
                               config):
    current_dynasty = 1
    crosslinking_start_shard = 0
    validators = genesis_validators

    indices_for_heights = get_new_shuffling(
        init_shuffling_seed,
        validators,
        current_dynasty,
        crosslinking_start_shard,
        config
    )
    # concatenate with itself to span 2*CYCLE_LENGTH
    indices_for_heights = indices_for_heights + indices_for_heights

    return CrystallizedState(
        validators=validators,
        epoch_number=0,
        indices_for_heights=indices_for_heights,
        last_justified_slot=0,
        justified_streak=0,
        last_finalized_slot=0,
        current_dynasty=current_dynasty,
        crosslinking_start_shard=crosslinking_start_shard,
        crosslink_records=[
            CrosslinkRecord(hash=b'\x00'*32, dynasty=0) for i in range(config['shard_count'])
        ],
        total_deposits=config['deposit_size']*len(validators),
        dynasty_seed=init_shuffling_seed,
        dynasty_seed_last_reset=1
    )


@pytest.fixture
def genesis_active_state(genesis_crystallized_state, cycle_length):
    recent_block_hashes = [b'\x00'*32] * cycle_length * 2

    return ActiveState(
        pending_attestations=[],
        recent_block_hashes=recent_block_hashes
    )


@pytest.fixture
def genesis_block():
    return Block(
        parent_hash=b'\x00'*32,
        slot_number=0,
        randao_reveal=b'\x00'*32,
        attestations=[],
        pow_chain_ref=b'\x00'*32,
        active_state_root=b'\x00'*32,
        crystallized_state_root=b'\x00'*32,
    )


@pytest.fixture
def mock_make_attestations(keymap, config):
    def mock_make_attestations(parent_state,
                               block,
                               attester_share=0.8):
        crystallized_state, active_state = parent_state
        cycle_length = config['cycle_length']

        in_epoch_slot_height = block.slot_number % cycle_length
        indices = crystallized_state.indices_for_heights[cycle_length + in_epoch_slot_height]

        print("Generating attestations for shards: %s" % len(indices))

        attestations = []
        for shard_and_committee in indices:
            shard_id = shard_and_committee.shard_id
            committee_indices = shard_and_committee.committee
            print("Generating attestation for shard %s" % shard_id)
            print("Committee size %s" % len(committee_indices))

            # Create attestation
            attestation = AttestationRecord(
                slot=block.slot_number,
                shard_id=shard_and_committee.shard_id,
                oblique_parent_hashes=[],
                shard_block_hash=blake(bytes(str(shard_id), 'utf-8')),
                attester_bitfield=get_empty_bitfield(len(committee_indices))
            )

            # Randomly pick indices to include
            is_attesting = [
                random.random() < attester_share for _ in range(len(committee_indices))
            ]
            # Proposer always attests
            is_attesting[0] = True

            # Generating signatures and aggregating result
            parent_hashes = get_signed_parent_hashes(
                active_state,
                block,
                attestation,
                config
            )
            message = blake(
                in_epoch_slot_height.to_bytes(8, byteorder='big') +
                b''.join(parent_hashes) +
                shard_id.to_bytes(2, byteorder='big') +
                attestation.shard_block_hash
            )
            sigs = [
                bls.sign(
                    message,
                    keymap[crystallized_state.validators[indice].pubkey]
                )
                for i, indice in enumerate(committee_indices) if is_attesting[i]
            ]
            attestation.aggregate_sig = bls.aggregate_sigs(sigs)
            print('Aggregated sig')

            attestation_bitfield = get_empty_bitfield(len(committee_indices))
            for i, attesting in enumerate(is_attesting):
                if attesting:
                    attestation_bitfield = set_voted(attestation_bitfield, i)
            attestation.attester_bitfield = attestation_bitfield
            print('Aggregate bitfield:', bin(int.from_bytes(attestation_bitfield, 'big')))

            attestations.append(attestation)

        return attestations
    return mock_make_attestations


@pytest.fixture
def mock_make_child(keymap, config):
    def mock_make_child(parent_state,
                        parent,
                        slot_number,
                        attestations=None):
        if attestations is None:
            attestations = []

        crystallized_state, active_state = parent_state
        block = Block(
            parent_hash=parent.hash,
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
            parent,
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
