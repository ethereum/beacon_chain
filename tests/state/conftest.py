import pytest
import random

from ssz import (
    serialize,
)

from beacon_chain.state.config import (
    BASE_REWARD_QUOTIENT,
    DEFAULT_END_DYNASTY,
    DEPOSIT_SIZE,
    CYCLE_LENGTH,
    MAX_VALIDATOR_COUNT,
    MIN_COMMITTEE_SIZE,
    MIN_DYNASTY_LENGTH,
    SHARD_COUNT,
    SLOT_DURATION,
    SQRT_E_DROP_TIME,
    generate_config,
)
from beacon_chain.state.attestation_record import (
    AttestationRecord,
)
from beacon_chain.state.block import (
    Block,
)
from beacon_chain.state.validator_record import (
    ValidatorRecord,
)
from beacon_chain.state.state_transition import (
    compute_state_transition,
)
from beacon_chain.state.genesis_helpers import (
    get_genesis_active_state,
    get_genesis_block,
    get_genesis_crystallized_state,
)
from beacon_chain.state.helpers import (
    get_hashes_to_sign,
    get_proposer_position,
)

import beacon_chain.utils.bls
from beacon_chain.utils.bitfield import (
    get_empty_bitfield,
    set_voted,
)
from beacon_chain.utils.blake import (
    blake,
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
def mock_bls(mocker, request):
    if 'noautofixt' in request.keywords:
        return

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
        'justified_slot': 5,
        'justified_block_hash': b'\x33'*32,
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
        'shard_and_committee_for_slots': [],
        'last_justified_slot': 100,
        'justified_streak': 10,
        'last_finalized_slot': 70,
        'current_dynasty': 4,
        'crosslink_records': [],
        'dynasty_seed': b'\x55'*32,
        'dynasty_start': 3,
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
        'slot': 0,
        'hash': b'\x43'*32,
    }


@pytest.fixture
def init_shuffling_seed():
    return DEFAULT_SHUFFLING_SEED


@pytest.fixture
def init_randao():
    return DEFAULT_RANDAO


@pytest.fixture
def base_reward_quotient():
    return BASE_REWARD_QUOTIENT


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
def min_dynasty_length():
    return MIN_DYNASTY_LENGTH


@pytest.fixture
def shard_count():
    return SHARD_COUNT


@pytest.fixture
def slot_duration():
    return SLOT_DURATION


@pytest.fixture
def sqrt_e_drop_time():
    return SQRT_E_DROP_TIME


@pytest.fixture
def config(base_reward_quotient,
           default_end_dynasty,
           deposit_size,
           cycle_length,
           max_validator_count,
           min_committee_size,
           min_dynasty_length,
           shard_count,
           slot_duration,
           sqrt_e_drop_time):
    return generate_config(
        base_reward_quotient=base_reward_quotient,
        default_end_dynasty=default_end_dynasty,
        deposit_size=deposit_size,
        cycle_length=cycle_length,
        max_validator_count=max_validator_count,
        min_committee_size=min_committee_size,
        min_dynasty_length=min_dynasty_length,
        shard_count=shard_count,
        slot_duration=slot_duration,
        sqrt_e_drop_time=sqrt_e_drop_time
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
    return get_genesis_crystallized_state(
        genesis_validators,
        init_shuffling_seed,
        config,
    )


@pytest.fixture
def genesis_active_state(config):
    return get_genesis_active_state(config)


@pytest.fixture
def genesis_block(genesis_active_state, genesis_crystallized_state):
    active_state_root = blake(serialize(genesis_active_state))
    crystallized_state_root = blake(serialize(genesis_crystallized_state))

    return get_genesis_block(
        active_state_root=active_state_root,
        crystallized_state_root=crystallized_state_root,
    )


@pytest.fixture
def mock_make_attestations(keymap, config):
    def mock_make_attestations(parent_state,
                               block,
                               attester_share=0.8):
        crystallized_state, active_state = parent_state
        cycle_length = config['cycle_length']

        in_cycle_slot_height = block.slot_number % cycle_length
        indices = crystallized_state.shard_and_committee_for_slots[
            cycle_length + in_cycle_slot_height
        ]

        print("Generating attestations for shards: %s" % len(indices))

        proposer_index_in_committee, proposer_shard_id = get_proposer_position(
            block,
            crystallized_state,
            config=config,
        )

        attestations = []
        for shard_and_committee in indices:
            shard_id = shard_and_committee.shard_id
            committee_indices = shard_and_committee.committee
            print("Generating attestation for shard %s" % shard_id)
            print("Committee size %s" % len(committee_indices))

            justified_slot = crystallized_state.last_justified_slot
            justified_block_hash = active_state.chain.get_block_by_slot_number(justified_slot).hash

            # Create attestation
            attestation = AttestationRecord(
                slot=block.slot_number,
                shard_id=shard_and_committee.shard_id,
                oblique_parent_hashes=[],
                shard_block_hash=blake(bytes(str(shard_id), 'utf-8')),
                attester_bitfield=get_empty_bitfield(len(committee_indices)),
                justified_slot=justified_slot,
                justified_block_hash=justified_block_hash,
            )

            # Randomly pick indices to include
            is_attesting = [
                random.random() < attester_share for _ in range(len(committee_indices))
            ]
            # Proposer always attests
            if shard_id == proposer_shard_id:
                is_attesting[proposer_index_in_committee] = True

            # Generating signatures and aggregating result
            parent_hashes = get_hashes_to_sign(
                active_state,
                block,
                config
            )
            message = blake(
                attestation.slot.to_bytes(8, byteorder='big') +
                b''.join(parent_hashes) +
                shard_id.to_bytes(2, byteorder='big') +
                attestation.shard_block_hash +
                attestation.justified_slot.to_bytes(8, byteorder='big')
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
