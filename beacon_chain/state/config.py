# DEFAULT_SWITCH_DYNASTY = 9999999999999999999
DEPOSIT_SIZE = 32  # ETH
END_EPOCH_GRACE_PERIOD = 8  # blocks
EPOCH_LENGTH = 64  # slots
MAX_VALIDATOR_COUNT = 2**22  # validators
MIN_COMMITTEE_SIZE = 128  # validators
SHARD_COUNT = 1024  # shards
SLOT_DURATION = 8  # seconds


def generate_config(*,
                    deposit_size=DEPOSIT_SIZE,
                    end_epoch_grace_period=END_EPOCH_GRACE_PERIOD,
                    epoch_length=EPOCH_LENGTH,
                    max_validator_count=MAX_VALIDATOR_COUNT,
                    min_committee_size=MIN_COMMITTEE_SIZE,
                    shard_count=SHARD_COUNT,
                    slot_duration=SLOT_DURATION):
    return {
        'deposit_size': deposit_size,
        'end_epoch_grace_period': end_epoch_grace_period,
        'epoch_length': epoch_length,
        'max_validator_count': max_validator_count,
        'min_committee_size': min_committee_size,
        'shard_count': shard_count,
        'slot_duration': slot_duration
    }


DEFAULT_CONFIG = generate_config()
