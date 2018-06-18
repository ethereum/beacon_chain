from .partial_crosslink_record import PartialCrosslinkRecord
from .recent_proposer_record import RecentProposerRecord


class ActiveState():

    fields = {
        # Block height
        'height': 'int64',
        # Global RANDAO beacon state
        'randao': 'hash32',
        # Which validators have made FFG votes this epoch (as a bitfield)
        'ffg_voter_bitfield': 'bytes',
        # Deltas to validator balances (to be processed at end of epoch)
        'balance_deltas': ['int48'],
        # Block attesters in the last epoch
        'recent_attesters': ['int24'],
        # Storing data about crosslinks-in-progress attempted in this epoch
        'partial_crosslinks': [PartialCrosslinkRecord],
        # Total number of skips (used to determine minimum timestamp)
        'total_skip_count': 'int64',
        # Block proposers in the last epoch
        'recent_proposers': [RecentProposerRecord]
    }
    defaults = {
        'height': 0,
        'randao': b'\x00'*32,
        'ffg_voter_bitfield': b'',
        'balance_deltas': [],
        'recent_attesters': [],
        'partial_crosslinks': [],
        'total_skip_count': 0,
        'recent_proposers': []
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
