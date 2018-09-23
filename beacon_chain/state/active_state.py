from typing import (  # noqa: F401
    Any,
    Dict,
)

from .attestation_record import AttestationRecord
from .chain import Chain


class ActiveState():

    fields = {
        # Attestations that have not yet been processed
        'pending_attestations': [AttestationRecord],
        # Most recent 2*CYCLE_LENGTH block hashes, older to newer
        'recent_block_hashes': ['hash32'],
    }
    defaults = {
        'pending_attestations': [],
        'recent_block_hashes': [],
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

        # block_vote_cache is not part of protocol state
        # is used as a helper cache to aid in doing the cycle init calculations
        if 'block_vote_cache' in kwargs:
            self.block_vote_cache = kwargs['block_vote_cache']
        else:
            self.block_vote_cache = {}

        # chain is not part of protocol state
        # is used as helper class to aid in doing state transition
        if 'chain' in kwargs:
            self.chain = kwargs['chain']
        else:
            self.chain = Chain()

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

    @property
    def num_pending_attestations(self):
        return len(self.pending_attestations)

    @property
    def num_recent_block_hashes(self):
        return len(self.recent_block_hashes)
