from typing import (  # noqa: F401
    Any,
    Dict,
)


class RecentProposerRecord():
    fields = {
        # Proposer index
        'index': 'uint24',
        # New RANDAO commitment
        'randao_commitment': 'hash32',
        # Balance delta
        'balance_delta': 'uint24'
    }
    defaults = {
        'randao_commitment': b'\x00'*32,
        'balance_delta': 0
    }  # type: Dict[str, Any]

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)
