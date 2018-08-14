
class ValidatorRecord():
    fields = {
        # The validator's public key
        'pubkey': 'int256',
        # What shard the validator's balance will be sent to after withdrawal
        'withdrawal_shard': 'int16',
        # And what address
        'withdrawal_address': 'address',
        # The validator's current RANDAO beacon commitment
        'randao_commitment': 'hash32',
        # Current balance
        'balance': 'int64',
        # Dynasty where the validator is inducted
        'start_dynasty': 'int64',
        # Dynasty where the validator leaves
        'end_dynasty': 'int64'
    }

    defaults = {}

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
