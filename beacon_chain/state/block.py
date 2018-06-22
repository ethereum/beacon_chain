from beacon_chain.utils.blake import blake
from beacon_chain.utils.bls import verify, sign
from beacon_chain.utils.simpleserialize import serialize

from .aggregate_vote import AggregateVote


class Block():
    fields = {
        # Hash of the parent block
        'parent_hash': 'hash32',
        # Number of skips (for the full PoS mechanism)
        'skip_count': 'int64',
        # Randao commitment reveal
        'randao_reveal': 'hash32',
        # Bitmask of who participated in the block notarization committee
        'attestation_bitfield': 'bytes',
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
        'attestation_bitfield': b'',
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

    @property
    def num_attestation_aggregate_sig(self):
        return len(self.attestation_aggregate_sig)

    @property
    def num_shard_aggregate_votes(self):
        return len(self.shard_aggregate_votes)

    @property
    def num_sig(self):
        return len(self.sig)
