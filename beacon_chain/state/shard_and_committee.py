from typing import (  # noqa: F401
    Any,
    Dict,
)


class ShardAndCommittee():
    fields = {
        # The shard ID
        'shard_id': 'uint16',
        # Validator indices
        'committee': ['uint24'],
    }

    defaults = {
        'shard_id': 0,
        'committee': [],
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)
