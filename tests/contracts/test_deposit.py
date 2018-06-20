import pytest
from conftest import REGISTRATION_DEPOSIT


@pytest.mark.parametrize(
    'success,amount_deposit',
    [
        (True, REGISTRATION_DEPOSIT),
        (False, REGISTRATION_DEPOSIT - 1),
        (False, REGISTRATION_DEPOSIT + 1)
    ]
)
def test_deposit(tester, a0, w3, success, amount_deposit, assert_tx_failed):
    base_tester, registration = tester

    call = registration.functions.deposit(b'\x00'*32, 43, a0, b'\x00'*32)
    if success:
        assert call.transact({"value": w3.toWei(amount_deposit, "ether")})
    else:
        assert_tx_failed(
            lambda: call.transact({"value": w3.toWei(amount_deposit, "ether")})
        )
