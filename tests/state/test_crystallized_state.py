import pytest

from beacon_chain.state.crystallized_state import (
    CrystallizedState,
)
from beacon_chain.state.crosslink_record import (
    CrosslinkRecord,
)

from tests.state.helpers import (
    mock_validator_record,
)


@pytest.mark.parametrize(
    'param,default_value',
    [
        ('active_validators', []),
        ('queued_validators', []),
        ('exited_validators', []),
        ('current_epoch', 0),
        ('current_shuffling', []),
        ('last_justified_epoch', 0),
        ('last_finalized_epoch', 0),
        ('current_dynasty', 0),
        ('next_shard', 0),
        ('current_checkpoint', b'\x00'*32),
        ('crosslink_records', []),
        ('total_deposits', 0),
        ('dynasty_seed', b'\x00'*32),
        ('dynasty_seed_last_reset', 0),
    ]
)
def test_defaults(param, default_value, sample_crystallized_state_params):
    del sample_crystallized_state_params[param]
    crystallized_state = CrystallizedState(**sample_crystallized_state_params)

    assert getattr(crystallized_state, param) == default_value


def test_num_properties(config):
    active_validators = [
        mock_validator_record(pubkey, config)
        for pubkey in range(2)
    ]
    queued_validators = [
        mock_validator_record(pubkey, config)
        for pubkey in range(3)
    ]
    exited_validators = [
        mock_validator_record(pubkey, config)
        for pubkey in range(4)
    ]
    crosslink_records = [
        CrosslinkRecord(hash=b'\x00'*32, epoch=0) for i in range(5)
    ]

    crystallized_state = CrystallizedState(
        active_validators=active_validators,
        queued_validators=queued_validators,
        exited_validators=exited_validators,
        current_shuffling=active_validators,
        crosslink_records=crosslink_records,
    )

    assert crystallized_state.num_active_validators == 2
    assert crystallized_state.num_queued_validators == 3
    assert crystallized_state.num_exited_validators == 4
    assert crystallized_state.num_crosslink_records == 5
