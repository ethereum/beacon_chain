from .attestation_record import AttestationRecord

class ActiveState():

    fields = {
        'attestations': [AttestationRecord],
        # Total quantity of wei that attested for the most recent checkpoint
        'total_attester_deposits': 'int64',
        # Who attested
        'attester_bitfield': 'bytes',
    }
    defaults = {
        'attestations': [],
        'total_attester_deposits': 0,
        'attester_bitfield': b'',
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    @property
    def num_attestations(self):
        return len(self.attestations)
