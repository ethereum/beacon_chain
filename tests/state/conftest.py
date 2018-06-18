import pytest


@pytest.fixture
def sample_active_state_params():
    return {
        'height': 30,
        'randao': b'\x35'*32,
        'ffg_voter_bitfield': b'\x42\x60',
        'balance_deltas': [1, 2, 3],
        'partial_crosslinks': [],
        'total_skip_count': 33
    }
