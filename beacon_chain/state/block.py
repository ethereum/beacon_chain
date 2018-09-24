from typing import (  # noqa: F401
    Any,
    Dict,
)

from ssz import (
    serialize,
)

from beacon_chain.utils.blake import blake
from beacon_chain.state.constants import (
    ZERO_HASH32,
)

from .attestation_record import AttestationRecord


class Block():
    fields = {
        # Hash of the parent block
        'parent_hash': 'hash32',
        # Slot number (for the PoS mechanism)
        'slot_number': 'uint64',
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
    }  # type: Dict[str, Any]

    defaults = {
        'parent_hash': ZERO_HASH32,
        'slot_number': 0,
        'randao_reveal': ZERO_HASH32,
        'attestations': [],
        'pow_chain_ref': ZERO_HASH32,
        'active_state_root': ZERO_HASH32,
        'crystallized_state_root': ZERO_HASH32,
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

    @property
    def hash(self):
        return blake(serialize(self))

    @property
    def num_attestations(self):
        return len(self.attestations)
