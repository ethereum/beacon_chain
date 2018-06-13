from beacon_chain.blake import blake
from beacon_chain.bls import verify, sign
from beacon_chain.simpleserialize import serialize


class AggregateVote():
    fields = {
        'shard_id': 'int16',
        'checkpoint_hash': 'hash32',
        'signer_bitmask': 'bytes',
        'aggregate_sig': ['int256']
    }
    defaults = {
        'shard_id': 0,
        'checkpoint_hash': b'\x00'*32,
        'signer_bitmask': b'',
        'aggregate_sig': [0, 0],
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))


class Block():
    fields = {
        # Hash of the parent block
        'parent_hash': 'hash32',
        # Number of skips (for the full PoS mechanism)
        'skip_count': 'int64',
        # Randao commitment reveal
        'randao_reveal': 'hash32',
        # Bitmask of who participated in the block notarization committee
        'attestation_bitmask': 'bytes',
        # Their aggregate sig
        'attestation_aggregate_sig': ['int256'],
        # Shard aggregate votes
        'shard_aggregate_votes': [AggregateVote],
        # Reference to main chain block
        'main_chain_ref': 'hash32',
        # Hash of the state
        'state_hash': 'bytes',
        # Signature from signer
        'sig': ['int256']
    }

    defaults = {
        'parent_hash': b'\x00'*32,
        'skip_count': 0,
        'randao_reveal': b'\x00'*32,
        'attestation_bitmask': b'',
        'attestation_aggregate_sig': [0, 0],
        'shard_aggregate_votes': [],
        'main_chain_ref': b'\x00'*32,
        'state_hash': b'\x00'*32,
        'sig': [0, 0]
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def sign(self, key):
        self.sig = [0, 0]
        self.sig = list(sign(serialize(self), key))

    def verify(self, pub):
        zig = self.sig
        self.sig = [0, 0]
        o = verify(serialize(self), pub, tuple(zig))
        self.sig = zig
        return o

    @property
    def hash(self):
        return blake(serialize(self))


class ValidatorRecord():
    fields = {
        # The validator's public key
        'pubkey': 'int256',
        # What shard the validator's balance will be sent to after withdrawal
        'return_shard': 'int16',
        # And what address
        'return_address': 'address',
        # The validator's current RANDAO beacon commitment
        'randao_commitment': 'hash32',
        # Current balance
        'balance': 'int64',
        # Dynasty where the validator can (be inducted | be removed | withdraw)
        'switch_dynasty': 'int64'
    }
    defaults = {}

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))


class CheckpointRecord():

    fields = {
        # What shard is the crosslink being made for
        'shard_id': 'int16',
        # Hash of the block
        'checkpoint_hash': 'hash32',
        # Which of the eligible voters are voting for it (as a bitmask)
        'voter_bitmask': 'bytes'
    }
    defaults = {}

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults, k
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))


class ActiveState():

    fields = {
        # Block height
        'height': 'int64',
        # Global RANDAO beacon state
        'randao': 'hash32',
        # Which validators have made FFG votes this epoch (as a bitmask)
        'ffg_voter_bitmask': 'bytes',
        # Deltas to validator balances (to be processed at end of epoch)
        'balance_deltas': ['int32'],
        # Storing data about crosslinks-in-progress attempted in this epoch
        'checkpoints': [CheckpointRecord],
        # Total number of skips (used to determine minimum timestamp)
        'total_skip_count': 'int64'
    }
    defaults = {
        'height': 0,
        'randao': b'\x00'*32,
        'ffg_voter_bitmask': b'',
        'balance_deltas': [],
        'checkpoints': [],
        'total_skip_count': 0
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))


class CrosslinkRecord():
    fields = {
        # What epoch the crosslink was submitted in
        'epoch': 'int64',
        # The block hash
        'hash': 'hash32'
    }
    defaults = {'epoch': 0, 'hash': b'\x00'*32}

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))


class CrystallizedState():
    fields = {
        # List of active validators
        'active_validators': [ValidatorRecord],
        # List of joined but not yet inducted validators
        'queued_validators': [ValidatorRecord],
        # List of removed validators pending withdrawal
        'exited_validators': [ValidatorRecord],
        # The permutation of validators used to determine who cross-links
        # what shard in this epoch
        'current_shuffling': ['int24'],
        # The current epoch
        'current_epoch': 'int64',
        # The last justified epoch
        'last_justified_epoch': 'int64',
        # The last finalized epoch
        'last_finalized_epoch': 'int64',
        # The current dynasty
        'dynasty': 'int64',
        # The next shard that assignment for cross-linking will start from
        'next_shard': 'int16',
        # The current FFG checkpoint
        'current_checkpoint': 'hash32',
        # Records about the most recent crosslink for each shard
        'crosslink_records': [CrosslinkRecord],
        # Total balance of deposits
        'total_deposits': 'int256'
    }
    defaults = {
        'active_validators': [],
        'queued_validators': [],
        'exited_validators': [],
        'current_shuffling': ['int24'],
        'current_epoch': 0,
        'last_justified_epoch': 0,
        'last_finalized_epoch': 0,
        'dynasty': 0,
        'next_shard': 0,
        'current_checkpoint': b'\x00'*32,
        'crosslink_records': [],
        'total_deposits': 0
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
