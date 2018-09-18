import pytest

from ssz.ssz import (
    to_dict
)


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
    class foo:
        fields = {name: typ for name, typ, _ in field_data}
        defaults = {name: value for name, _, value in field_data}

    o = foo()
    for name, _, value in field_data:
        setattr(o, name, value)

    assert to_dict(o) == {name: value for name, _, value in field_data}
