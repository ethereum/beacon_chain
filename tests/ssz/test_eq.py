import pytest

from ssz.ssz import (
    eq
)


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
