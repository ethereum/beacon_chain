from beacon_chain.state.config import (
    DEFAULT_CONFIG,
)
from beacon_chain.state.block import Block
from beacon_chain.state.validator_record import (
    ValidatorRecord,
)


def mock_validator_record(pubkey, start_dynasty=0, config=DEFAULT_CONFIG):
    return ValidatorRecord(
        pubkey=pubkey,
        withdrawal_shard=0,
        withdrawal_address=pubkey.to_bytes(32, 'big')[-20:],
        randao_commitment=b'\x55'*32,
        balance=config['deposit_size'],
        start_dynasty=start_dynasty,
        end_dynasty=config['default_end_dynasty']
    )


def get_pseudo_chain(length):
    """Get a pseudo chain, only slot_number and parent_hash are valid.
    """
    blocks = []
    for slot in range(length * 3):
        blocks.append(
            Block(
                slot_number=slot,
                parent_hash=blocks[slot-1].hash if slot > 0 else b'00'*32
            )
        )

    return blocks
