from typing import (  # noqa: F401
    Any,
    Dict,
)

from beacon_chain.state.constants import (
    ZERO_HASH32,
)


class AttestationRecord():
    fields = {
        'slot': 'uint64',
        'shard_id': 'uint16',
        'oblique_parent_hashes': ['hash32'],
        'shard_block_hash': 'hash32',
        'attester_bitfield': 'bytes',
        'justified_slot': 'uint64',
        'justified_block_hash': 'hash32',
        'aggregate_sig': ['uint256'],
    }
    defaults = {
        'slot': 0,
        'shard_id': 0,
        'oblique_parent_hashes': [],
        'shard_block_hash': ZERO_HASH32,
        'attester_bitfield': b'',
        'justified_slot': 0,
        'justified_block_hash': ZERO_HASH32,
        'aggregate_sig': [0, 0],
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)
