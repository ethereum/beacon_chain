from beacon_chain.state.crystallized_state import (
    CrystallizedState,
)
from beacon_chain.state.crosslink_record import (
    CrosslinkRecord,
)

from tests.state.helpers import (
    mock_validator_record,
)


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
