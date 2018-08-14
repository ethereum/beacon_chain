from beacon_chain.utils.blake import blake
from beacon_chain.utils.simpleserialize import serialize

from .attestation_record import AttestationRecord


class Block():
    fields = {
        # Hash of the parent block
        'parent_hash': 'hash32',
        # Slot number (for the PoS mechanism)
        'slot_number': 'int64',
        # Randao commitment reveal
        'randao_reveal': 'hash32',
        # Attestations
        'attestations': [AttestationRecord],
        # Reference to PoW chain block
        'pow_chain_ref': 'hash32',
        # Hash of the active state
        'active_state_root': 'hash32',
        # Hash of the crystallized state
        'crystallized_state_root': 'hash32',
    }

    defaults = {
        'parent_hash': b'\x00'*32,
        'slot_number': 0,
        'randao_reveal': b'\x00'*32,
        'attestations': [],
        'pow_chain_ref': b'\x00'*32,
        'active_state_root': b'\x00'*32,
        'crystallized_state_root': b'\x00'*32,
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    @property
    def hash(self):
        return blake(serialize(self))

    @property
    def num_attestations(self):
        return len(self.attestations)
