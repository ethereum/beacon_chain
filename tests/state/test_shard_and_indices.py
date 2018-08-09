import pytest

from beacon_chain.state.shard_and_indices import (
    ShardAndIndices,
)


@pytest.mark.parametrize(
    'param,default_value',
    [
        ('shard_id', 0),
        ('validators', []),
    ]
)
def test_defaults(param, default_value, sample_shard_and_indices_params):
    del sample_shard_and_indices_params[param]
    shard_and_indices = ShardAndIndices(**sample_shard_and_indices_params)

    assert getattr(shard_and_indices, param) == default_value
