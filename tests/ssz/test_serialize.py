import pytest

from ssz import (
    serialize,
)


@pytest.mark.parametrize(
    'value, typ, data',
    [
        (5, 'int8', b'\x05'),
        (7, 'int16', b'\x00\x07'),
        (8, 'int32', b'\x00\x00\x00\x08'),
        (15, 'int64', b'\x00\x00\x00\x00\x00\x00\x00\x0f'),
        (130, 'int128', b'\x00' * 15 + b'\x82'),
        (225, 'int256', b'\x00' * 31 + b'\xe1'),
        (b'\x35'*20, 'address', b'\x35'*20),
        (b'\x35'*32, 'hash32', b'\x35'*32),
        (b'cow', 'bytes', b'\x00\x00\x00\x03cow'),
        ([3, 4, 5], ['int8'], b'\x00\x00\x00\x03\x03\x04\x05'),
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
        (-5, 'uint32'),
    ]
)
def test_failed_serialization(value, typ):
    with pytest.raises(Exception):
        serialize(value, typ)
