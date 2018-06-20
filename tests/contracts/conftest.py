import os
import pytest
import eth_tester
from eth_tester import (
    EthereumTester,
    PyEVMBackend
)
from web3.providers.eth_tester import (
    EthereumTesterProvider,
)
from web3 import (
    Web3,
)
from web3.contract import (
    ConciseContract,
)

from vyper import (
    compiler,
    utils as vyper_utils,
)

REGISTRATION_DEPOSIT = 32


def get_dirs(path):
    own_dir = os.path.dirname(os.path.realpath(__file__))
    abs_contract_path = os.path.realpath(
        os.path.join(own_dir, '..', '..', 'contracts'))
    sub_dirs = [x[0] for x in os.walk(abs_contract_path)]
    extra_args = ' '.join(['{}={}'.format(d.split('/')[-1], d)
                           for d in sub_dirs])
    path = '{}/{}'.format(abs_contract_path, path)
    return path, extra_args


@pytest.fixture
def registration_code():
    with open(get_dirs('validator_registration.v.py')[0]) as f:
        return f.read()


@pytest.fixture
def base_tester():
    return EthereumTester(PyEVMBackend())


@pytest.fixture
def a0(base_tester):
    return base_tester.get_accounts()[0]


@pytest.fixture
def w3(base_tester):
    web3 = Web3(EthereumTesterProvider(base_tester))
    return web3


@pytest.fixture
def tester(w3, base_tester, registration_code):
    contract_bytecode = compiler.compile(registration_code)
    contract_abi = compiler.mk_full_signature(registration_code)
    registration = w3.eth.contract(
        abi=contract_abi, bytecode=contract_bytecode)
    tx_hash = registration.constructor().transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    registration_deployed = w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=contract_abi
    )
    return base_tester, registration_deployed


@pytest.fixture
def assert_tx_failed(base_tester):
    def assert_tx_failed(function_to_test, exception=eth_tester.exceptions.TransactionFailed):
        snapshot_id = base_tester.take_snapshot()
        with pytest.raises(exception):
            function_to_test()
        base_tester.revert_to_snapshot(snapshot_id)
    return assert_tx_failed
