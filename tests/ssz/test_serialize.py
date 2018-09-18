import pytest

from ssz import (
    serialize,
)


@pytest.mark.parametrize(
    'value, typ, data',
    [
        (5, 'int8', b'\x05'),
        (2**32-3, 'int40', b'\x00\xff\xff\xff\xfd'),
        (b'\x35'*20, 'address', b'\x35'*20),
        (b'\x35'*32, 'hash32', b'\x35'*32),
        (b'cow', 'bytes', b'\x00\x00\x00\x03cow'),
    ]
)
def test_basic_serialization(value, typ, data):
    assert serialize(value, typ) == data


@pytest.mark.parametrize(
    'value, typ',
    [
        (b'', 'byte'),
        (b'', 'hash16'),
        (0, 0),
    ]
)
def test_failed_serialization(value, typ):
    with pytest.raises(Exception):
        serialize(value, typ)
