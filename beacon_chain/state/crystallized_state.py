from .crosslink_record import CrosslinkRecord
from .validator_record import ValidatorRecord


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
        'current_shuffling': [],
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

        # Check if num_active_validators == num_current_shuffling
        assert self.num_active_validators == len(self.current_shuffling)

    @property
    def num_active_validators(self):
        return len(self.active_validators)

    @property
    def num_queued_validators(self):
        return len(self.queued_validators)

    @property
    def num_exited_validators(self):
        return len(self.exited_validators)

    @property
    def num_crosslink_records(self):
        return len(self.crosslink_records)
