import pytest
import random

from beacon_chain.state.config import (
    ATTESTER_COUNT,
    ATTESTER_REWARD,
    DEFAULT_BALANCE,
    DEFAULT_SWITCH_DYNASTY,
    EPOCH_LENGTH,
    MAX_VALIDATORS,
    SHARD_COUNT,
    generate_config
)
from beacon_chain.state.active_state import (
    ActiveState,
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
from beacon_chain.state.state_transition import (
    compute_state_transition,
    get_attesters_and_signer,
    get_crosslink_aggvote_msg,
    get_shard_attesters,
    get_shuffling,
    state_hash,
)

import beacon_chain.utils.bls as bls
from beacon_chain.utils.blake import (
    blake,
)
from beacon_chain.utils.simpleserialize import (
    serialize,
)


DEFAULT_SHUFFLING_SEED = b'\35'*32
DEFAULT_RANDAO = b'\45'*32
DEFAULT_NUM_VALIDATORS = 40


@pytest.fixture
def sample_active_state_params():
    return {
        'height': 30,
        'randao': b'\x35'*32,
        'ffg_voter_bitfield': b'\x42\x60',
        'balance_deltas': [1, 2, 3],
        'recent_attesters': [0, 2, 10],
        'partial_crosslinks': [],
        'total_skip_count': 33,
        'recent_proposers': []
    }


@pytest.fixture
def sample_recent_proposer_record_params():
    return {
        'index': 10,
        'randao_commitment': b'\x43'*32,
        'balance_delta': 3
    }


@pytest.fixture
def init_shuffling_seed():
    return DEFAULT_SHUFFLING_SEED


@pytest.fixture
def init_randao():
    return DEFAULT_RANDAO


@pytest.fixture
def attester_count():
    return ATTESTER_COUNT


@pytest.fixture
def attester_reward():
    return ATTESTER_REWARD


@pytest.fixture
def epoch_length():
    return EPOCH_LENGTH


@pytest.fixture
def shard_count():
    return SHARD_COUNT


@pytest.fixture
def default_balance():
    return DEFAULT_BALANCE


@pytest.fixture
def max_validators():
    return MAX_VALIDATORS


@pytest.fixture
def config(attester_count,
           attester_reward,
           epoch_length,
           shard_count,
           default_balance,
           max_validators):
    return generate_config(
        attester_count=attester_count,
        attester_reward=attester_reward,
        epoch_length=epoch_length,
        shard_count=shard_count,
        default_balance=default_balance,
        max_validators=max_validators
    )


@pytest.fixture
def num_validators():
    return DEFAULT_NUM_VALIDATORS


@pytest.fixture
def init_validator_keys(pubkeys, num_validators):
    return pubkeys[:num_validators]


@pytest.fixture
def genesis_crystallized_state(init_validator_keys,
                               init_shuffling_seed):
    return CrystallizedState(
        active_validators=[ValidatorRecord(
            pubkey=pub,
            withdrawal_shard=0,
            withdrawal_address=blake(pub.to_bytes(32, 'big'))[-20:],
            randao_commitment=b'\x55'*32,
            balance=DEFAULT_BALANCE,
            switch_dynasty=DEFAULT_SWITCH_DYNASTY
        ) for pub in init_validator_keys],
        queued_validators=[],
        exited_validators=[],
        current_shuffling=get_shuffling(init_shuffling_seed, len(init_validator_keys)),
        current_epoch=1,
        last_justified_epoch=0,
        last_finalized_epoch=0,
        dynasty=1,
        next_shard=0,
        current_checkpoint=blake(b'insert EOS constitution here'),
        crosslink_records=[
            CrosslinkRecord(hash=b'\x00'*32, epoch=0) for i in range(SHARD_COUNT)
        ],
        total_deposits=DEFAULT_BALANCE*len(init_validator_keys)
    )


@pytest.fixture
def genesis_active_state(genesis_crystallized_state,
                         init_randao):
    return ActiveState(
        height=1,
        randao=init_randao,
        ffg_voter_bitfield=bytearray((len(genesis_crystallized_state.active_validators) + 7) // 8),
        balance_deltas=[],
        partial_crosslinks=[],
        total_skip_count=0
    )


@pytest.fixture
def genesis_block(genesis_crystallized_state, genesis_active_state):
    return Block(
        parent_hash=b'\x00'*32,
        skip_count=0,
        randao_reveal=b'\x00'*32,
        attestation_bitfield=b'',
        attestation_aggregate_sig=[0, 0],
        shard_aggregate_votes=[],
        main_chain_ref=b'\x00'*32,
        state_hash=state_hash(genesis_crystallized_state, genesis_active_state),
        sig=[0, 0]
    )


# Mock makes a block based upon the params passed indices
# This block does not have a calculated state root and is unsigned
@pytest.fixture
def make_unfinished_block(keymap, config):
    def make_unfinished_block(parent_state,
                              parent,
                              skips,
                              attester_share=0.8,
                              crosslink_shards=[]):
        crystallized_state, active_state = parent_state
        parent_attestation = serialize(parent)
        indices, main_signer = get_attesters_and_signer(
            crystallized_state,
            active_state,
            skips,
            config
        )

        print('Selected indices: %r' % indices)
        print('Selected main signer: %d' % main_signer)

        # Randomly pick indices to include
        bitfield = [1 if random.random() < attester_share else 0 for i in indices]
        # Attestations
        sigs = [
            bls.sign(
                parent_attestation,
                keymap[crystallized_state.active_validators[indices[i]].pubkey]
            )
            for i in range(len(indices)) if bitfield[i]
        ]
        attestation_aggregate_sig = bls.aggregate_sigs(sigs)
        print('Aggregated sig')

        attestation_bitfield = bytearray((len(bitfield)-1) // 8 + 1)
        for i, b in enumerate(bitfield):
            attestation_bitfield[i//8] ^= (128 >> (i % 8)) * b
        print('Aggregate bitfield:', bin(int.from_bytes(attestation_bitfield, 'big')))

        # Randomly pick indices to include for crosslinks
        shard_aggregate_votes = []
        for shard, crosslinker_share in crosslink_shards:
            print('Making crosslink in shard %d' % shard)
            indices = get_shard_attesters(crystallized_state, shard, config)
            print('Indices: %r' % indices)
            bitfield = [1 if random.random() < crosslinker_share else 0 for i in indices]
            bitmask = bytearray((len(bitfield)+7) // 8)
            for i, b in enumerate(bitfield):
                bitmask[i//8] ^= (128 >> (i % 8)) * b
            print('Bitmask:', bin(int.from_bytes(bitmask, 'big')))
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
                for i in range(len(indices)) if bitfield[i]
            ]
            v = AggregateVote(
                shard_id=shard,
                shard_block_hash=shard_block_hash,
                signer_bitmask=bitmask,
                aggregate_sig=list(bls.aggregate_sigs(sigs))
            )
            shard_aggregate_votes.append(v)
        print('Added %d shard aggregate votes' % len(crosslink_shards))

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
        return block, main_signer
    return make_unfinished_block


@pytest.fixture
def mock_make_child(keymap, make_unfinished_block, config):
    def mock_make_child(parent_state,
                        parent,
                        skips,
                        attester_share=0.8,
                        crosslink_shards=[]):
        crystallized_state, active_state = parent_state
        block, main_signer = make_unfinished_block(
            parent_state,
            parent,
            skips,
            attester_share,
            crosslink_shards
        )
        print('Generated preliminary block header')

        new_crystallized_state, new_active_state = compute_state_transition(
            (crystallized_state, active_state),
            parent,
            block,
            verify_sig=False,
            config=config
        )
        print('Calculated state transition')

        if crystallized_state == new_crystallized_state:
            block.state_hash = blake(parent.state_hash[:32] + blake(serialize(new_active_state)))
        else:
            block.state_hash = blake(blake(serialize(new_crystallized_state)) + blake(serialize(new_active_state)))
        # Main signature
        block.sign(keymap[crystallized_state.active_validators[main_signer].pubkey])
        print('Signed')

        return block, new_crystallized_state, new_active_state
    return mock_make_child
