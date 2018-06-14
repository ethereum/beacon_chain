from .checkpoint_record import CheckpointRecord


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
