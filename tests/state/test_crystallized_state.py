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


@pytest.mark.parametrize(
    'expected', [(0), (1), (5)]
)
def test_num_active_validators(expected):
    validators = [mock_validator_record(pubkey) for pubkey in range(expected)]
    crystallized_state = CrystallizedState(
        active_validators=validators,
    )

    assert crystallized_state.num_active_validators == expected


@pytest.mark.parametrize(
    'expected', [(0), (1), (5)]
)
def test_num_queued_validators(expected):
    validators = [mock_validator_record(pubkey) for pubkey in range(expected)]
    crystallized_state = CrystallizedState(
        queued_validators=validators,
    )

    assert crystallized_state.num_queued_validators == expected


@pytest.mark.parametrize(
    'expected', [(0), (1), (5)]
)
def test_num_exited_validators(expected):
    validators = [mock_validator_record(pubkey) for pubkey in range(expected)]
    crystallized_state = CrystallizedState(
        exited_validators=validators,
    )

    assert crystallized_state.num_exited_validators == expected


@pytest.mark.parametrize(
    'expected', [(0), (1), (5)]
)
def test_num_crosslink_records(expected):
    crosslink_records = [
        CrosslinkRecord() for i in range(expected)
    ]
    crystallized_state = CrystallizedState(
        crosslink_records=crosslink_records,
    )

    assert crystallized_state.num_crosslink_records == expected
