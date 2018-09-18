import pytest

from ssz.ssz import (
    deserialize
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
