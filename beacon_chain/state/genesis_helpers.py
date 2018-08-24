from typing import (
    Any,
    Dict,
    List,
    TYPE_CHECKING,
)

from beacon_chain.beacon_typing.custom import (
    Hash32,
    ShardId,
)

from .active_state import ActiveState
from .block import Block
from .constants import (
    ZERO_HASH32,
)
from .crosslink_record import CrosslinkRecord
from .crystallized_state import CrystallizedState
from .helpers import (
    get_new_shuffling,
)

if TYPE_CHECKING:
    from .validator_record import ValidatorRecord  # noqa: F401


def get_genesis_active_state(config: Dict[str, Any]) -> ActiveState:
    recent_block_hashes = [ZERO_HASH32] * config['cycle_length'] * 2

    return ActiveState(
        pending_attestations=[],
        recent_block_hashes=recent_block_hashes
    )


def get_genesis_crystallized_state(
        validators: List['ValidatorRecord'],
        init_shuffling_seed: Hash32,
        config: Dict[str, Any]) -> CrystallizedState:

    current_dynasty = 1
    crosslinking_start_shard = ShardId(0)

    indices_for_slots = get_new_shuffling(
        init_shuffling_seed,
        validators,
        current_dynasty,
        crosslinking_start_shard,
        config=config,
    )
    # concatenate with itself to span 2*CYCLE_LENGTH
    indices_for_slots = indices_for_slots + indices_for_slots

    total_deposits = config['deposit_size'] * len(validators)

    return CrystallizedState(
        validators=validators,
        last_state_recalc=0,
        indices_for_slots=indices_for_slots,
        last_justified_slot=0,
        justified_streak=0,
        last_finalized_slot=0,
        current_dynasty=current_dynasty,
        crosslinking_start_shard=crosslinking_start_shard,
        crosslink_records=[
            CrosslinkRecord(hash=ZERO_HASH32, dynasty=0)
            for i
            in range(config['shard_count'])
        ],
        total_deposits=total_deposits,
        dynasty_seed=init_shuffling_seed,
        dynasty_seed_last_reset=1,
    )


def get_genesis_block(active_state_root: Hash32,
                      crystallized_state_root: Hash32) -> Block:
    return Block(
        parent_hash=ZERO_HASH32,
        slot_number=0,
        randao_reveal=ZERO_HASH32,
        attestations=[],
        pow_chain_ref=ZERO_HASH32,
        active_state_root=active_state_root,
        crystallized_state_root=crystallized_state_root,
    )
