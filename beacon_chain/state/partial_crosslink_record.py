from typing import (  # noqa: F401
    Any,
    Dict,
)


class PartialCrosslinkRecord():

    fields = {
        # What shard is the crosslink being made for
        'shard_id': 'int16',
        # Hash of the block
        'shard_block_hash': 'hash32',
        # Which of the eligible voters are voting for it (as a bitfield)
        'voter_bitfield': 'bytes'
    }
    defaults = {
        'shard_id': 0,
        'shard_block_hash': b'\x00'*32,
        'voter_bitfield': b'',
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults, k
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)
