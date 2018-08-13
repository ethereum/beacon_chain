DEFAULT_END_DYNASTY = 9999999999999999999
DEPOSIT_SIZE = 32  # ETH
CYCLE_LENGTH = 64  # slots
MAX_VALIDATOR_COUNT = 2**22  # validators
MIN_COMMITTEE_SIZE = 128  # validators
SHARD_COUNT = 1024  # shards
SLOT_DURATION = 8  # seconds


def generate_config(*,
                    default_end_dynasty=DEFAULT_END_DYNASTY,
                    deposit_size=DEPOSIT_SIZE,
                    cycle_length=CYCLE_LENGTH,
                    max_validator_count=MAX_VALIDATOR_COUNT,
                    min_committee_size=MIN_COMMITTEE_SIZE,
                    shard_count=SHARD_COUNT,
                    slot_duration=SLOT_DURATION):
    return {
        'default_end_dynasty': default_end_dynasty,
        'deposit_size': deposit_size,
        'cycle_length': cycle_length,
        'max_validator_count': max_validator_count,
        'min_committee_size': min_committee_size,
        'shard_count': shard_count,
        'slot_duration': slot_duration
    }


DEFAULT_CONFIG = generate_config()
