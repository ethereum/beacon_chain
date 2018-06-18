import pytest


@pytest.fixture
def sample_active_state_params():
    return {
        'height': 30,
        'randao': b'\x35'*32,
        'ffg_voter_bitfield': b'\x42\x60',
        'balance_deltas': [1, 2, 3],
        'recent_attesters': [0, 2, 10],
        'partial_crosslinks': [],
        'total_skip_count': 33,
        'recent_proposers': []
    }


@pytest.fixture
def sample_recent_proposer_record_params():
    return {
        'index': 10,
        'randao_commitment': b'\x43'*32,
        'balance_delta': 3
    }
