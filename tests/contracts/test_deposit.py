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

    call = registration_contract.functions.deposit(b'\x00'*32, 43, a0, b'\x00'*32)
    if success:
        assert call.transact({"value": w3.toWei(amount_deposit, "ether")})
    else:
        assert_tx_failed(
            lambda: call.transact({"value": w3.toWei(amount_deposit, "ether")})
        )
