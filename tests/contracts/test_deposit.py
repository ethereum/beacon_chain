import pytest


@pytest.mark.parametrize(
    'success,amount_deposit',
    [
        (True, 32),
        (True, 1),
        (False, 0),
        (False, 33)
    ]
)
def test_deposit_amount(registration_contract, w3, success, amount_deposit, assert_tx_failed):

    call = registration_contract.functions.deposit(b'\x10' * 100)
    if success:
        assert call.transact({"value": w3.toWei(amount_deposit, "ether")})
    else:
        assert_tx_failed(
            lambda: call.transact({"value": w3.toWei(amount_deposit, "ether")})
        )


def test_deposit_log(registration_contract, a0, w3):
    log_filter = registration_contract.events.Eth1Deposit.createFilter(
        fromBlock='latest')

    deposit_parameters = b'\x10' * 100
    deposit_amount = 32 * 10**9
    registration_contract.functions.deposit(
        deposit_parameters).transact({"value": w3.toWei(deposit_amount, "gwei")})

    logs = log_filter.get_new_entries()
    assert len(logs) == 1
    log = logs[0]['args']

    amount_bytes8 = deposit_amount.to_bytes(8, 'big')
    timestamp_bytes8 = int(w3.eth.getBlock(w3.eth.blockNumber)['timestamp']).to_bytes(8, 'big')
    assert log['previous_receipt_root'] == b'\x00' * 32
    assert log['data'] == amount_bytes8 + timestamp_bytes8 + deposit_parameters
    assert log['deposit_count'] == 0
