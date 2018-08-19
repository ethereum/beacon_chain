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
        ('validators', []),
        ('last_state_recalc', 0),
        ('indices_for_heights', []),
        ('last_justified_slot', 0),
        ('justified_streak', 0),
        ('last_finalized_slot', 0),
        ('current_dynasty', 0),
        ('crosslinking_start_shard', 0),
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
def test_num_validators(expected):
    validators = [mock_validator_record(pubkey) for pubkey in range(expected)]
    crystallized_state = CrystallizedState(
        validators=validators,
    )

    assert crystallized_state.num_validators == expected


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
