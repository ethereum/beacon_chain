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
        # The current epoch
        'current_epoch': 'int64',
        # The permutation of the validators that
        # determines who participates in what
        # committee and at what height
        'current_shuffling': ['int24'],
        # The last justified epoch
        'last_justified_epoch': 'int64',
        # The last finalized epoch
        'last_finalized_epoch': 'int64',
        # The current dynasty
        'current_dynasty': 'int64',
        # The next shard that crosslinking assignment will start from
        'next_shard': 'int16',
        # The current FFG checkpoint
        'current_checkpoint': 'hash32',
        # Records about the most recent crosslink for each shard
        'crosslink_records': [CrosslinkRecord],
        # Total balance of deposits
        'total_deposits': 'int256',
        # Used to select the committees for each shard
        'dynasty_seed': 'hash32',
        # Last epoch the crosslink seed was reset
        'dynasty_seed_last_reset': 'int64',
    }
    defaults = {
        'active_validators': [],
        'queued_validators': [],
        'exited_validators': [],
        'current_epoch': 0,
        'current_shuffling': [],
        'last_justified_epoch': 0,
        'last_finalized_epoch': 0,
        'current_dynasty': 0,
        'next_shard': 0,
        'current_checkpoint': b'\x00'*32,
        'crosslink_records': [],
        'total_deposits': 0,
        'dynasty_seed': b'\x00'*32,
        'dynasty_seed_last_reset': 0,
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
