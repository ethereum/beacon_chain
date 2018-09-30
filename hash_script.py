from beacon_chain.state.validator_record import ValidatorRecord
from beacon_chain.state.genesis_helpers import get_genesis_crystallized_state
from ssz import serialize


validators = [ValidatorRecord() for i in range(1000000)]
c = get_genesis_crystallized_state(validators, b'\x00' * 32)

serialize(c)