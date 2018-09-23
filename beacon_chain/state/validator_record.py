from typing import (  # noqa: F401
    Any,
    Dict,
)


class ValidatorRecord():
    fields = {
        # The validator's public key
        'pubkey': 'uint256',
        # What shard the validator's balance will be sent to after withdrawal
        'withdrawal_shard': 'uint16',
        # And what address
        'withdrawal_address': 'address',
        # The validator's current RANDAO beacon commitment
        'randao_commitment': 'hash32',
        # Current balance
        'balance': 'uint128',
        # Dynasty where the validator is inducted
        'start_dynasty': 'uint64',
        # Dynasty where the validator leaves
        'end_dynasty': 'uint64'
    }

    defaults = {
        'pubkey': b'',
        'withdrawal_shard': 0,
        'withdrawal_address': b'\x00'*20,
        'randao_commitment': b'\x00'*32,
        'balance': 0,
        'start_dynasty': 0,
        'end_dynasty': 0,
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)
