from beacon_chain.utils.blake import blake


class AttestationRecord():
    fields = {
        'slot': 'int64',
        'parent_hash': 'hash32',
        'checkpoint_hash': 'hash32',
        'shard_id': 'int16',
        'shard_block_hash': 'hash32',
        'attester_bitfield': 'bytes',
        'aggregate_sig': ['int256'],
    }
    defaults = {
        'slot': 0,
        'parent_hash': b'\x00'*32,
        'checkpoint_hash': b'\x00'*32,
        'shard_id': 0,
        'shard_block_hash': b'\x00'*32,
        'attester_bitfield': b'',
        'aggregate_sig': [0, 0],
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
