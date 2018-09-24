from typing import (  # noqa: F401
    Any,
    Dict,
    List,
)

from .crosslink_record import CrosslinkRecord
from .shard_and_committee import ShardAndCommittee
from .validator_record import ValidatorRecord

from .helpers import get_active_validator_indices


class CrystallizedState():
    fields = {
        # List of validators
        'validators': [ValidatorRecord],
        # Last CrystallizedState recalculation
        'last_state_recalc': 'uint64',
        # What active validators are part of the attester set
        # at what height, and in what shard. Starts at slot
        # last_state_recalc - CYCLE_LENGTH
        'shard_and_committee_for_slots': [[ShardAndCommittee]],
        # The last justified slot
        'last_justified_slot': 'uint64',
        # Number of consecutive justified slots ending at this one
        'justified_streak': 'uint64',
        # The last finalized slot
        'last_finalized_slot': 'uint64',
        # The current dynasty
        'current_dynasty': 'uint64',
        # Records about the most recent crosslink for each shard
        'crosslink_records': [CrosslinkRecord],
        # Used to select the committees for each shard
        'dynasty_seed': 'hash32',
        # start of the current dynasty
        'dynasty_start': 'uint64',
    }
    defaults = {
        'validators': [],
        'last_state_recalc': 0,
        'shard_and_committee_for_slots': [],
        'last_justified_slot': 0,
        'justified_streak': 0,
        'last_finalized_slot': 0,
        'current_dynasty': 0,
        'crosslink_records': [],
        'dynasty_seed': b'\x00'*32,
        'dynasty_start': 0,
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

    @property
    def active_validator_indices(self) -> List[int]:
        return get_active_validator_indices(
            self.current_dynasty,
            self.validators
        )

    @property
    def total_deposits(self) -> int:
        return sum(
            map(
                lambda index: self.validators[index].balance,
                self.active_validator_indices
            )
        )

    @property
    def num_validators(self) -> int:
        return len(self.validators)

    @property
    def num_crosslink_records(self) -> int:
        return len(self.crosslink_records)
