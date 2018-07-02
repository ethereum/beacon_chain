from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)
from beacon_chain.state.crystallized_state import (
    CrystallizedState,
)
from beacon_chain.state.validator_record import (
    ValidatorRecord,
)
from beacon_chain.state.state_transition import (
    get_shuffling,
)


def mock_crystallized_state(
        genesis_crystallized_state,
        init_shuffling_seed,
        next_shard,
        active_validators=None,
        config=DEFAULT_CONFIG):

    crystallized_state = CrystallizedState()
    crystallized_state.next_shard = next_shard
    if active_validators is not None:
        crystallized_state.active_validators = active_validators
        crystallized_state.current_shuffling = get_shuffling(
            init_shuffling_seed,
            len(active_validators),
            config=config,
        )
    return crystallized_state


def mock_validator_record(pubkey, config):
    return ValidatorRecord(
        pubkey=pubkey,
        withdrawal_shard=0,
        withdrawal_address=pubkey.to_bytes(32, 'big')[-20:],
        randao_commitment=b'\x55'*32,
        balance=config['default_balance'],
        switch_dynasty=config['default_switch_dynasty']
    )

