import pytest

from ssz.ssz import (
    deserialize
)


@pytest.mark.parametrize(
    'value, typ, data',
    [
        (5, 'int8', b'\x05'),
        (7, 'int16', b'\x00\x07'),
        (9, 'int32', b'\x00\x00\x00\x09'),
        (15, 'int64', b'\x00\x00\x00\x00\x00\x00\x00\x0f'),
        (130, 'int128', b'\x00' * 15 + b'\x82'),
        (225, 'int256', b'\x00' * 31 + b'\xe1'),
        (b'\x35'*20, 'address', b'\x35'*20),
        (b'\x35'*32, 'hash32', b'\x35'*32),
        (b'cow', 'bytes', b'\x00\x00\x00\x03cow'),
        ([3, 4, 5], ['int8'], b'\x00\x00\x00\x03\x03\x04\x05'),
    ]
)
def test_basic_deserialization(value, typ, data):
    assert deserialize(data, typ) == value


@pytest.mark.parametrize(
    'data, typ',
    [
        (b'randombytes', 'hash31'),
        (b'randombytes', 'bytes32'),
        (b'randombytes', 'unknown'),
        (b'randombytes', ['unknown']),
    ]
)
def test_deserialization_unknown_type(data, typ):
    with pytest.raises(Exception):
        deserialize(data, typ)
