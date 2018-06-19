import pytest


@pytest.mark.parametrize(
    'epoch_length',
    [
        (3),
    ]
)
def test_height_updates(genesis_crystallized_state,
                        genesis_active_state,
                        genesis_block,
                        mock_make_child,
                        epoch_length,
                        config):
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


@pytest.mark.parametrize(
    'epoch_length',
    [
        (3),
        (5),
    ]
)
def test_recent_proposer_is_added(genesis_crystallized_state,
                                  genesis_active_state,
                                  genesis_block,
                                  mock_make_child,
                                  epoch_length,
                                  config):
    crystallized_state = genesis_crystallized_state
    active_state = genesis_active_state
    parent_block = genesis_block

    assert len(active_state.recent_proposers) == 0

    # 0th epoch is atypical
    for i in range(epoch_length - 1):
        child_block, crystallized_state, active_state = mock_make_child(
            (crystallized_state, active_state),
            parent_block,
            0,
            0.8,
            []
        )

        # starts at height 1, no proposer yet at this height
        assert len(active_state.recent_proposers) == (active_state.height - 1) % epoch_length
        parent_block = child_block

    # test epochs after 0th epoch
    for _ in range(epoch_length * 2):
        child_block, crystallized_state, active_state = mock_make_child(
            (crystallized_state, active_state),
            parent_block,
            0,
            0.8,
            []
        )

        # starts each cycle at 1 proposer
        assert len(active_state.recent_proposers) == 1 + (active_state.height - 1) % epoch_length
        parent_block = child_block
