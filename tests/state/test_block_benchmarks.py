import time
import pytest

from ssz import (
    serialize,
)

from beacon_chain.state.state_transition import (
    compute_state_transition,
)


@pytest.mark.parametrize(
    (
        'num_validators'
    ),
    [
        # (100, 1000, 50, 10, 10),
        # (1000, 1000, 20, 10, 100),
        # (10**5, 10**5, 64, 128, 1024),
        # (10**6, 10**6, 64, 128, 1024),
        # (10**7, 10**7, 64, 128, 1024),
        # (10**8, 10**8, 64, 128, 1024),
        # (31250),
        # (312500),
        (3125000)
        # (312500, 312500, 64, 128, 1024),
        # (4062500, 4062500, 64, 128, 1024),

    ],
)
def test_state_transition_integration(genesis_crystallized_state,
                                      genesis_active_state,
                                      genesis_block,
                                      mock_make_child,
                                      mock_make_attestations,
                                      config):
    c = genesis_crystallized_state
    a = genesis_active_state
    block = genesis_block

    attestations = mock_make_attestations(
        (c, a),
        block,
        attester_share=1.0
    )
    block2, c2, a2 = mock_make_child((c, a), block, 1, attestations)

    t_start = time.time()
    compute_state_transition((c, a), block, block2, config=config)
    t_end = time.time()

    print(
        "Normal block with %s attestations of size %s processed in %.4f sec (%s total validators)" %
        (
            len(attestations),
            len(c.shard_and_committee_for_slots[attestations[0].slot][0].committee),
            (t_end - t_start),
            len(c.validators)
        )
    )
    s_start = time.time()
    serialized_c_state = serialize(c)
    s_end = time.time()
    print('Crystallized state length:', len(serialized_c_state))
    print("time to serialize: %.4f" % (s_end - s_start))
    print('Active state length:', len(serialize(a)))
    print('Block size:', len(serialize(block2)))

    print(
        "%s,%s,%s,%s,%.4f,%s,%s,%s" %
        (
            len(attestations),
            len(c.shard_and_committee_for_slots[attestations[0].slot][0].committee),
            len(c.validators),
            len(c.validators) * config['deposit_size'] // 10**18,
            (t_end - t_start),
            len(serialized_c_state),
            len(serialize(a2)),
            len(serialize(block2))
        )
    )

        # "Normal block with %s attestations of size %s processed in %.4f sec (%s total validators)" %
        # (
            # len(attestations),
            # len(c.shard_and_committee_for_slots[attestations[0].slot][0].committee),
            # (t_end - t_start),
            # len(c.validators)
        # )
    # )
 


    # attestations = mock_make_attestations(
        # (c2, a2),
        # block2,
        # attester_share=1.0
    # )
    # block3, c3, a3 = mock_make_child((c2, a2), block2, 2, attestations)

    # t_start = time.time()
    # compute_state_transition((c2, a2), block2, block3, config=config)
    # t_end = time.time()

    # print(
        # "Normal block with %s attestations of size %s processed in %.4f sec" %
        # (
            # len(attestations),
            # len(c.shard_and_committee_for_slots[attestations[0].slot][0].committee),
            # (t_end - t_start)
        # )
    # )

    # shards = [
        # shard_and_commitee.shard_id
        # for slot in range(64)
        # for shard_and_commitee in c.shard_and_committee_for_slots[slot]
    # ]
    # print(shards)
