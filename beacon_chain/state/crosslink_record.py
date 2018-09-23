from typing import (  # noqa: F401
    Any,
    Dict,
)


class CrosslinkRecord():
    fields = {
        # What dynasty the crosslink was submitted in
        'dynasty': 'uint64',
        # slot during which crosslink was added
        'slot': 'uint64',
        # The block hash
        'hash': 'hash32',
    }
    defaults = {
        'dynasty': 0,
        'slot': 0,
        'hash': b'\x00'*32,
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)
