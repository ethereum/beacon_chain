from typing import (
    Dict,
    NewType,
    Union,
)


BlockVoteCache = Dict[str, Dict[str, Union[str, bytes, int]]]
Hash32 = NewType('Hash32', bytes)
ShardId = NewType('ShardId', int)
