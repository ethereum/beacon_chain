import hash_ssz
from beacon_chain.state import crystallized_state as cs
from ssz import ssz
import time
from hashlib import blake2b

def hash(x):
    return blake2b(x).digest()[:32]

v = cs.ValidatorRecord(pubkey=3**160, withdrawal_shard=567, withdrawal_address=b'\x35' * 20, randao_commitment=b'\x57' * 20, balance=32 * 10**18, start_dynasty=7, end_dynasty=17284)
c = cs.CrosslinkRecord(dynasty=4, slot=12847, hash=b'\x67' * 32)
cr_stubs = [c for i in range(1024)]

def make_crystallized_state(valcount):
    sc_stub = cs.ShardAndCommittee(shard_id=1, committee=list(range(valcount // 1024)))
    sc_stubs = [[sc_stub for i in range(16)] for i in range(64)]
    c = cs.CrystallizedState(
        validators=[v for i in range(valcount)],
        last_state_recalc=1,
        shard_and_committee_for_slots=sc_stubs,
        last_justified_slot=12744,
        justified_streak=98,
        last_finalized_slot=1724,
        current_dynasty=19824,
        crosslink_records = cr_stubs,
        dynasty_seed=b'\x98' * 32,
        dynasty_start=124
    )
    return c

def time_test(valcount):
    c = make_crystallized_state(valcount)
    a = time.time()
    h = hash_ssz.hash_ssz(c)
    return(time.time() - a)

def encoded_length(valcount):
    c = make_crystallized_state(valcount)
    return len(ssz.serialize(c))

def hash_time_test(valcount):
    c = make_crystallized_state(valcount)
    a = time.time()
    s = ssz.serialize(c)
    a2 = time.time()
    h = hash(s)
    return(a2 - a, time.time() - a2)

if __name__ == '__main__':
    print(time_test(2**18))
