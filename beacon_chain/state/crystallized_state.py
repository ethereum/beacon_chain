from .crosslink_record import CrosslinkRecord
from .shard_and_committee import ShardAndCommittee
from .validator_record import ValidatorRecord


class CrystallizedState():
    fields = {
        # List of validators
        'validators': [ValidatorRecord],
        # Last CrystallizedState recalculation
        'last_state_recalc': 'int64',
        # What active validators are part of the attester set
        # at what height, and in what shard. Starts at slot
        # last_state_recalc - CYCLE_LENGTH
        'indices_for_heights': [[ShardAndCommittee]],
        # The last justified slot
        'last_justified_slot': 'int64',
        # Number of consecutive justified slots ending at this one
        'justified_streak': 'int64',
        # The last finalized slot
        'last_finalized_slot': 'int64',
        # The current dynasty
        'current_dynasty': 'int64',
        # The next shard that crosslinking assignment will start from
        'crosslinking_start_shard': 'int16',
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
        'validators': [],
        'last_state_recalc': 0,
        'indices_for_heights': [],
        'last_justified_slot': 0,
        'justified_streak': 0,
        'last_finalized_slot': 0,
        'current_dynasty': 0,
        'crosslinking_start_shard': 0,
        'crosslink_records': [],
        'total_deposits': 0,
        'dynasty_seed': b'\x00'*32,
        'dynasty_seed_last_reset': 0,
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    @property
    def num_validators(self):
        return len(self.validators)

    @property
    def num_crosslink_records(self):
        return len(self.crosslink_records)
