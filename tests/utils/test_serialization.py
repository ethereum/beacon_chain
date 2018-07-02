import pytest

from beacon_chain.state.active_state import (
    ActiveState,
)
from beacon_chain.state.partial_crosslink_record import (
    PartialCrosslinkRecord,
)
from beacon_chain.utils.simpleserialize import (
    serialize,
    deserialize,
    eq,
    to_dict,
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
    assert deserialize(data, typ) == value


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


def test_active_state_serialization():
    s = ActiveState()
    ds = deserialize(serialize(s, type(s)), type(s))
    assert eq(s, ds)

    s = ActiveState(
        partial_crosslinks=[
            PartialCrosslinkRecord(
                shard_id=42,
                shard_block_hash=b'\x55'*32,
                voter_bitfield=b'31337dawg'
            )
        ],
        height=555,
        randao=b'\x88'*32,
    )
    ds = deserialize(serialize(s, type(s)), type(s))
    assert eq(s, ds)


@pytest.mark.parametrize(
    'value, result',
    [
        ({}, {}),
        ({'a': 1, 'b': 2}, {'a': 1, 'b': 2}),
        ([], []),
        ([{'a': 1}, {'b': 2}], [{'a': 1}, {'b': 2}])
    ]
)
def test_to_dict(value, result):
    assert to_dict(value) == result


@pytest.mark.parametrize(
    'field_data',
    [
        [],
        [('a', 'int64', 1), ('b', 'hash32', b'two')]
    ]
)
def test_object_to_dict(field_data):
    class O:
        fields = {name: typ for name, typ, _ in field_data}
        defaults = {name: value for name, _, value in field_data}

    o = O()
    for name, _, value in field_data:
        setattr(o, name, value)

    assert to_dict(o) == {name: value for name, _, value in field_data}


@pytest.mark.parametrize(
    'left_fields, right_fields, equal',
    [
        [[], [], True],
        [[('a', 'int64', 0)], [('a', 'int64', 0)], True],
        [
            [('a', 'int64', 0), ('b', 'hash32', b'\x00' * 32)],
            [('a', 'int64', 0), ('b', 'hash32', b'\x00' * 32)],
            True
        ],
        [[('a', 'int64', 0)], [], False],
        [[('a', 'int64', 0)], [('a', 'int64', 1)], False],  # different value
        [[('a', 'int64', 0)], [('a', 'int32', 0)], False],  # different type
        [[('a', 'int64', 0)], [('b', 'int64', 0)], False],  # different name
    ]
)
def test_eq(left_fields, right_fields, equal):
    class LeftClass:
        fields = {name: typ for name, typ, _ in left_fields}
        defaults = {name: value for name, _, value in left_fields}

    class RightClass:
        fields = {name: typ for name, typ, _ in right_fields}
        defaults = {name: value for name, _, value in right_fields}

    left_object = LeftClass()
    for name, _, value in left_fields:
        setattr(left_object, name, value)

    right_object = RightClass()
    for name, _, value in right_fields:
        setattr(right_object, name, value)

    assert eq(left_object, right_object) == equal
    assert eq(right_object, left_object) == equal
