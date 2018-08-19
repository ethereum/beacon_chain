from .attestation_record import AttestationRecord


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
    }

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

    @property
    def num_pending_attestations(self):
        return len(self.pending_attestations)
