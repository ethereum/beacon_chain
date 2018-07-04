import pytest

from beacon_chain.state.state_transition import (
    get_shuffling,
    process_ffg_deposits,
    process_recent_attesters,
    process_recent_proposers,
)

from beacon_chain.state.crystallized_state import (
    CrystallizedState,
)
from beacon_chain.state.validator_record import (
    ValidatorRecord,
)
from beacon_chain.state.recent_proposer_record import (
    RecentProposerRecord,
)

from beacon_chain.utils.bitfield import (
    get_empty_bitfield,
    set_voted,
)


def test_height_updates(genesis_crystallized_state,
                        genesis_active_state,
                        genesis_block,
                        mock_make_child,
                        epoch_length):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block

    assert active_state.height == 1

    prev_height = active_state.height
    for _ in range(epoch_length * 2):
        child_block, crystallized_state, active_state = mock_make_child(
            (crystallized_state, active_state),
            parent_block,
            0,
            attester_share=0.8,
        )

        assert active_state.height == prev_height + 1
        prev_height = active_state.height


def test_recent_proposer_is_added(genesis_crystallized_state,
                                  genesis_active_state,
                                  genesis_block,
                                  mock_make_child,
                                  epoch_length):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block

    assert active_state.num_recent_proposers == 0

    for _ in range(epoch_length * 2):
        child_block, crystallized_state, active_state = mock_make_child(
            (crystallized_state, active_state),
            parent_block,
            0,
        )

        if active_state.height <= epoch_length:
            # 0th epoch starts at height 1 so no base proposer
            base = 0
        else:
            base = 1

        assert active_state.num_recent_proposers == \
            base + (active_state.height - 1) % epoch_length
        parent_block = child_block


# Test assumes that no FFG votes are cast so proposer reward is just form attestations
# `mock_make_child` currently does not cast any votes
# when FFG voting is added to function, this test will require FFG votes to be set to zero.
def test_proposer_balance_delta(genesis_crystallized_state,
                                genesis_active_state,
                                genesis_block,
                                mock_make_child,
                                epoch_length,
                                attester_count):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block

    child_block, crystallized_state, active_state = mock_make_child(
        (crystallized_state, active_state),
        parent_block,
        0,
        1.0  # full attestation
    )

    assert active_state.num_recent_proposers == 1
    assert active_state.recent_proposers[0].balance_delta == attester_count

    fraction_attested = 0.6
    child_block, crystallized_state, active_state = mock_make_child(
        (crystallized_state, active_state),
        parent_block,
        0,
        fraction_attested  # fractional attestation
    )

    assert active_state.num_recent_proposers == 2

    # count number of actual attesters
    bitfield = child_block.attestation_bitfield
    num_attesters = 0
    for i in range(len(bitfield)):
        num_attesters += bin(bitfield[i]).count("1")

    assert active_state.recent_proposers[-1].balance_delta == num_attesters


def test_recent_attesters_added(genesis_crystallized_state,
                                genesis_active_state,
                                genesis_block,
                                mock_make_child,
                                epoch_length,
                                attester_count):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block

    assert active_state.num_recent_attesters == 0

    for _ in range(epoch_length * 2):
        child_block, crystallized_state, active_state = mock_make_child(
            (crystallized_state, active_state),
            parent_block,
            0,
            1.0
        )

        if active_state.height <= epoch_length:
            # 0th epoch starts at height 1 so no base proposer
            base = 0
        else:
            base = 1

        assert active_state.num_recent_attesters == \
            (base + (active_state.height - 1) % epoch_length) * attester_count

        parent_block = child_block


def test_recent_attester_processing(genesis_crystallized_state, config, attester_reward):
    zero_deltas = process_recent_attesters(genesis_crystallized_state, [], config=config)
    assert len(zero_deltas) == genesis_crystallized_state.num_active_validators
    for delta in zero_deltas:
        assert delta == 0

    some_validators = [0, 5, 39]
    some_deltas = process_recent_attesters(
        genesis_crystallized_state,
        some_validators,
        config=config,
    )
    assert len(some_deltas) == genesis_crystallized_state.num_active_validators
    for i, delta in enumerate(some_deltas):
        if i in some_validators:
            assert delta == attester_reward
        else:
            assert delta == 0


def test_recent_proposer_processing(genesis_crystallized_state):
    zero_deltas = process_recent_proposers(genesis_crystallized_state, [])
    assert len(zero_deltas) == genesis_crystallized_state.num_active_validators
    for delta in zero_deltas:
        assert delta == 0

    some_proposers = [RecentProposerRecord(index=index, balance_delta=delta) for index, delta in [
        (0, 100),
        (5, 200),
        (39, 300),
    ]]
    some_indices = [some_proposer.index for some_proposer in some_proposers]
    some_deltas = process_recent_proposers(genesis_crystallized_state, some_proposers)
    for i, delta in enumerate(some_deltas):
        if i not in some_indices:
            assert delta == 0
    assert some_deltas[0] == 100
    assert some_deltas[5] == 200
    assert some_deltas[39] == 300


@pytest.mark.parametrize("balances, votes, justifying", [
    ([1, 1, 1], [True, True, True], True),
    ([1, 1, 1], [True, True, False], True),
    ([1, 1, 1], [True, False, True], True),
    ([1, 1, 1], [False, True, True], True),
    ([1, 1, 1], [True, False, False], False),
    ([1, 1, 1], [False, True, False], False),
    ([1, 1, 1], [False, False, True], False),
    ([1, 1, 1], [False, False, False], False),

    ([4, 1, 1], [True, False, False], True),
    ([4, 1, 1], [False, True, False], False),
    ([4, 1, 1], [False, False, True], False),
])
def test_ffg_vote_counting(balances, votes, justifying):
    validators = [ValidatorRecord(
        pubkey=0,
        withdrawal_shard=0,
        withdrawal_address=b'\x00' * 32,
        randao_commitment=b'\x55' * 32,
        balance=balance,
        switch_dynasty=1000
    ) for balance in balances]
    total_deposits = sum(balances)

    # first epoch
    crystallized_state1 = CrystallizedState(
        active_validators=validators,
        current_epoch=1,
        last_justified_epoch=0,
        last_finalized_epoch=0,
        total_deposits=total_deposits,
        current_shuffling=get_shuffling(b'', len(validators)),
    )

    bitfield = get_empty_bitfield(len(validators))
    for i, vote in enumerate(votes):
        if vote:
            bitfield = set_voted(bitfield, i)

    (
        _,
        total_vote_count,
        total_vote_deposit,
        justify,
        finalize
    ) = process_ffg_deposits(crystallized_state1, bitfield)
    assert total_vote_count == sum(int(vote) for vote in votes)
    assert total_vote_deposit == sum(balance for balance, vote in zip(balances, votes) if vote)
    assert justify == justifying
    assert finalize == justifying  # genesis is justified

    # epoch following unjustified epoch
    crystallized_state2 = CrystallizedState(
        active_validators=validators,
        current_epoch=2,
        last_justified_epoch=0,
        last_finalized_epoch=0,
        total_deposits=total_deposits,
        current_shuffling=get_shuffling(b'', len(validators)),
    )
    (
        _,
        total_vote_count,
        total_vote_deposit,
        justify,
        finalize
    ) = process_ffg_deposits(crystallized_state2, bitfield)
    assert justify == justifying
    assert not finalize

    # epoch following justified epoch
    crystallized_state3 = CrystallizedState(
        active_validators=validators,
        current_epoch=3,
        last_justified_epoch=2,
        last_finalized_epoch=0,
        total_deposits=total_deposits,
        current_shuffling=get_shuffling(b'', len(validators)),
    )
    (
        _,
        total_vote_count,
        total_vote_deposit,
        justify,
        finalize
    ) = process_ffg_deposits(crystallized_state3, bitfield)
    assert justify == justifying
    assert finalize == justifying
