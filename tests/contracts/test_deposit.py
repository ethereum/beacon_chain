import pytest


@pytest.mark.parametrize(
    'success,amount_deposit',
    [
        (True, 32),
        (False, 31),
        (False, 33),
        (False, 0)
    ]
)
def test_deposit(registration_contract, a0, w3, success, amount_deposit, assert_tx_failed):

    call = registration_contract.functions.deposit(
        b'\x00'*32,
        43,
        a0,
        b'\x00'*32)
    if success:
        assert call.transact({"value": w3.toWei(amount_deposit, "ether")})
    else:
        assert_tx_failed(
            lambda: call.transact({"value": w3.toWei(amount_deposit, "ether")})
        )


def test_no_reuse_of_pubkey(registration_contract, a0, w3, assert_tx_failed):

    call = registration_contract.functions.deposit(
        b'\x55'*32,
        43,
        a0,
        b'\x00'*32)

    # Register pubkey b'\x55'*32 once.
    assert call.transact({"value": w3.toWei(32, "ether")})

    # Register pubkey b'\x55'*32 twice would fail
    assert_tx_failed(
        lambda: call.transact({"value": w3.toWei(32, "ether")})
    )


def test_log_is_captured(registration_contract, a0, w3):
    log_filter = registration_contract.events.Deposit.createFilter(
        fromBlock='latest')

    registration_contract.functions.deposit(
        b'\x00'*32,
        43,
        a0,
        b'\x00'*32).transact({"value": w3.toWei(32, "ether")})

    logs = log_filter.get_new_entries()
    log = logs[0]['args']

    assert log['_pubkey'] == b'\x00'*32
    assert log['_withdrawal_shard_id'] == 43
    assert log['_withdrawal_address'] == a0
    assert log['_randao_commitment'] == b'\x00'*32
