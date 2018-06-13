import pytest
import random

import beacon_chain.bls as bls
from beacon_chain.blake import blake
from beacon_chain.utils import (
    DEFAULT_BALANCE,
    DEFAULT_SWITCH_DYNASTY,
    SHARD_COUNT,
    compute_state_transition,
    get_attesters_and_signer,
    get_checkpoint_aggvote_msg,
    get_shard_attesters,
    get_shuffling,
    state_hash,
)
from beacon_chain.full_pos import (
    ActiveState,
    AggregateVote,
    Block,
    CrosslinkRecord,
    CrystallizedState,
    ValidatorRecord,
)
from beacon_chain.simpleserialize import serialize


DEFAULT_SHUFFLING_SEED = b'\35'*32
DEFAULT_RANDAO = b'\45'*32


@pytest.fixture
def privkeys():
    return [int.from_bytes(blake(str(i).encode('utf-8'))[:4], 'big') for i in range(1000)]


@pytest.fixture
def keymap(privkeys):
    keymap = {}
    for i, k in enumerate(privkeys):
        keymap[bls.privtopub(k)] = k
        if i % 50 == 0:
            print("Generated %d keys" % i)
    return keymap


@pytest.fixture
def pubkeys(keymap):
    return keymap.keys()


@pytest.fixture
def init_shuffling_seed():
    return DEFAULT_SHUFFLING_SEED


@pytest.fixture
def init_randao():
    return DEFAULT_RANDAO


@pytest.fixture
def genesis_crystallized_state(pubkeys,
                               init_shuffling_seed):
    return CrystallizedState(
        active_validators=[ValidatorRecord(
            pubkey=pub,
            return_shard=0,
            return_address=blake(pub.to_bytes(32, 'big'))[-20:],
            randao_commitment=b'\x55'*32,
            balance=DEFAULT_BALANCE,
            switch_dynasty=DEFAULT_SWITCH_DYNASTY
        ) for pub in pubkeys],
        queued_validators=[],
        exited_validators=[],
        current_shuffling=get_shuffling(init_shuffling_seed, len(pubkeys)),
        current_epoch=1,
        last_justified_epoch=0,
        last_finalized_epoch=0,
        dynasty=1,
        next_shard=0,
        current_checkpoint=blake(b'insert EOS constitution here'),
        crosslink_records=[
            CrosslinkRecord(hash=b'\x00'*32, epoch=0) for i in range(SHARD_COUNT)
        ],
        total_deposits=DEFAULT_BALANCE*len(pubkeys)
    )


@pytest.fixture
def genesis_active_state(genesis_crystallized_state,
                         init_randao):
    return ActiveState(
        height=1,
        randao=init_randao,
        ffg_voter_bitmask=bytearray((len(genesis_crystallized_state.active_validators) + 7) // 8),
        balance_deltas=[],
        checkpoints=[],
        total_skip_count=0
    )


@pytest.fixture
def genesis_block(genesis_crystallized_state, genesis_active_state):
    return Block(
        parent_hash=b'\x00'*32,
        skip_count=0,
        randao_reveal=b'\x00'*32,
        attestation_bitmask=b'',
        attestation_aggregate_sig=[0, 0],
        shard_aggregate_votes=[],
        main_chain_ref=b'\x00'*32,
        state_hash=state_hash(genesis_crystallized_state, genesis_active_state),
        sig=[0, 0]
    )


@pytest.fixture
def mock_make_child(keymap):
    def mock_make_child(parent_state, parent, skips, attester_share=0.8, checkpoint_shards=[]):
        crystallized_state, active_state = parent_state
        parent_attestation_hash = parent.hash
        validator_count = len(crystallized_state.active_validators)
        indices, main_signer = get_attesters_and_signer(crystallized_state, active_state, skips)
        print('Selected indices: %r' % indices)
        print('Selected main signer: %d' % main_signer)
        # Randomly pick indices to include
        bitfield = [1 if random.random() < attester_share else 0 for i in indices]
        # Attestations
        sigs = [bls.sign(parent_attestation_hash, keymap[crystallized_state.active_validators[indices[i]].pubkey])
                for i in range(len(indices)) if bitfield[i]]
        attestation_aggregate_sig = bls.aggregate_sigs(sigs)
        print('Aggregated sig')
        attestation_bitmask = bytearray((len(bitfield)-1) // 8 + 1)
        for i, b in enumerate(bitfield):
            attestation_bitmask[i//8] ^= (128 >> (i % 8)) * b
        print('Aggregate bitmask:', bin(int.from_bytes(attestation_bitmask, 'big')))
        # Randomly pick indices to include for checkpoints
        shard_aggregate_votes = []
        for shard, crosslinker_share in checkpoint_shards:
            print('Making crosslink in shard %d' % shard)
            indices = get_shard_attesters(crystallized_state, shard)
            print('Indices: %r' % indices)
            bitfield = [1 if random.random() < crosslinker_share else 0 for i in indices]
            bitmask = bytearray((len(bitfield)+7) // 8)
            for i, b in enumerate(bitfield):
                bitmask[i//8] ^= (128 >> (i % 8)) * b
            print('Bitmask:', bin(int.from_bytes(bitmask, 'big')))
            checkpoint = blake(bytes([shard]))
            checkpoint_attestation_hash = get_checkpoint_aggvote_msg(shard, checkpoint, crystallized_state)
            sigs = [bls.sign(checkpoint_attestation_hash, keymap[crystallized_state.active_validators[indices[i]].pubkey])
                    for i in range(len(indices)) if bitfield[i]]
            v = AggregateVote(shard_id=shard,
                              checkpoint_hash=checkpoint,
                              signer_bitmask=bitmask,
                              aggregate_sig=list(bls.aggregate_sigs(sigs)))
            shard_aggregate_votes.append(v)
        print('Added %d shard aggregate votes' % len(checkpoint_shards))
        # State calculations
        o = Block(parent_hash=parent.hash,
                  skip_count=skips,
                  randao_reveal=blake(str(random.random()).encode('utf-8')),
                  attestation_bitmask=attestation_bitmask,
                  attestation_aggregate_sig=list(attestation_aggregate_sig),
                  shard_aggregate_votes=shard_aggregate_votes,
                  main_chain_ref=b'\x00'*32,
                  state_hash=b'\x00'*64)
        print('Generated preliminary block header')
        new_crystallized_state, new_active_state = \
            compute_state_transition((crystallized_state, active_state), parent, o, verify_sig=False)
        print('Calculated state transition')
        if crystallized_state == new_crystallized_state:
            o.state_hash = blake(parent.state_hash[:32] + blake(serialize(new_active_state)))
        else:
            o.state_hash = blake(blake(serialize(new_crystallized_state)) + blake(serialize(new_active_state)))
        # Main signature
        o.sign(keymap[crystallized_state.active_validators[main_signer].pubkey])
        print('Signed')
        return o, new_crystallized_state, new_active_state
    return mock_make_child

