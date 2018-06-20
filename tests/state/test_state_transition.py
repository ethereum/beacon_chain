import pytest


def test_height_updates(genesis_crystallized_state,
                        genesis_active_state,
                        genesis_block,
                        mock_make_child,
                        epoch_length):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block

    print("NUM_VALIDATORS: %s" % len(crystallized_state.active_validators))
    assert active_state.height == 1

    prev_height = active_state.height
    for _ in range(epoch_length * 2):
        child_block, crystallized_state, active_state = mock_make_child(
            (crystallized_state, active_state),
            parent_block,
            0,
            0.8,
            []
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

    assert len(active_state.recent_proposers) == 0

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

        assert len(active_state.recent_proposers) == \
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

    assert len(active_state.recent_proposers) == 1
    assert active_state.recent_proposers[0].balance_delta == attester_count

    fraction_attested = 0.6
    child_block, crystallized_state, active_state = mock_make_child(
        (crystallized_state, active_state),
        parent_block,
        0,
        fraction_attested  # fractional attestation
    )

    assert len(active_state.recent_proposers) == 2
    assert active_state.recent_proposers[-1].balance_delta <= attester_count * fraction_attested


def test_recent_attesters_added(genesis_crystallized_state,
                                genesis_active_state,
                                genesis_block,
                                mock_make_child,
                                epoch_length,
                                attester_count):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block

    assert len(active_state.recent_attesters) == 0

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

        assert len(active_state.recent_attesters) == \
            (base + (active_state.height - 1) % epoch_length) * attester_count

        parent_block = child_block
