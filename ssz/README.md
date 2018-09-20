# Simple Serialize (SSZ)

Simple Serialize is a serialization protocol described by Vitalik Buterin with design rationale outlined [here](https://github.com/ethereum/beacon_chain/tree/master/ssz). --update this link to reflect design rationale document when common document is ready--

SSZ To-Do:  
[X]Move tests to tests/ssz  
[  ][Add full test coverage for supported types](https://github.com/ethereum/beacon_chain/issues/100)  
[  ][Refactor ssz.py](https://github.com/ethereum/beacon_chain/issues/100)

## Serialization Examples
```
int8: 5 --> b’\x05’
bytes: b'cow' --> b'\x00\x00\x00\x03cow'
address: b'\x35'*20 --> b’55555555555555555555’
hash32: b'\x35'*32 --> b’55555555555555555555555555555555’
list['int8']: [3, 4, 5] --> b'\x00\x00\x00\x03\x03\x04\x05'
```
## Python Usage

```serialize(val, typ)``` takes 1 to 2 arguments. ```serialize(val, typ)``` can minimally take a value and perform the standard operation, or ```serialize(val, typ)``` can take a value and explicit type to shorten the length of serialization. If ```typ``` is not an explicitly supported type, output data will default to 4 bytes.

```deserialize(data, typ)``` takes 2 arguments: data and type and deserializes into the previously serialized value

### Example

In a general case, usage is as follows:

```python
typ = 'int8'
value = 5
print(serialize(value, typ))
```
the above would print
b’\x05’

and to deserialize the data and print our original value we would simply use
```python
typ = 'int8'
print(deserialize(b'\x05', typ))
```
the above would print
5  
Note: deserializing always requires type

The above can easily be extended to more complex cases.

The following is a case that was previously used as the primary test case for simple serialize
```python
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
```
In the above test case, all assertions are true
