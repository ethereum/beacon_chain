
class AggregateVote():
    fields = {
        'shard_id': 'int16',
        'shard_block_hash': 'hash32',
        'signer_bitfield': 'bytes',
        'aggregate_sig': ['int256']
    }
    defaults = {
        'shard_id': 0,
        'shard_block_hash': b'\x00'*32,
        'signer_bitfield': b'',
        'aggregate_sig': [0, 0],
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
