from typing import (
    Any,
)


class AttestationRecord():
    fields = {
        'slot': 'int64',
        'shard_id': 'int16',
        'oblique_parent_hashes': ['hash32'],
        'shard_block_hash': 'hash32',
        'attester_bitfield': 'bytes',
        'aggregate_sig': ['int256'],
    }
    defaults = {
        'slot': 0,
        'shard_id': 0,
        'oblique_parent_hashes': [],
        'shard_block_hash': b'\x00'*32,
        'attester_bitfield': b'',
        'aggregate_sig': [0, 0],
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)
