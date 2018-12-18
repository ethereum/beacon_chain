import pytest

import eth_utils

from tests.contracts.conftest import (
    MAX_DEPOSIT,
    MIN_DEPOSIT,
    DEPOSIT_CONTRACT_TREE_DEPTH,
)


def compute_merkle_root(w3, leaf_nodes):
    assert len(leaf_nodes) >= 1
    empty_node = b'\x00' * 32
    child_nodes = leaf_nodes[:]
    for i in range(DEPOSIT_CONTRACT_TREE_DEPTH):
        parent_nodes = []
        if len(child_nodes) % 2 == 1:
            child_nodes.append(empty_node)
        for j in range(0, len(child_nodes), 2):
            parent_nodes.append(w3.sha3(child_nodes[j] + child_nodes[j+1]))
        child_nodes = parent_nodes
    return child_nodes[0]


@pytest.mark.parametrize(
    'success,amount_deposit',
    [
        (True, MAX_DEPOSIT),
        (True, MIN_DEPOSIT),
        (False, MIN_DEPOSIT - 1),
        (False, MAX_DEPOSIT + 1)
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
        fromBlock='latest',
    )

    deposit_input = b'\x10' * 100
    deposit_amount = MAX_DEPOSIT * eth_utils.denoms.gwei
    registration_contract.functions.deposit(
        deposit_input,
    ).transact({"value": w3.toWei(deposit_amount, "gwei")})

    logs = log_filter.get_new_entries()
    assert len(logs) == 1
    log = logs[0]['args']

    amount_bytes8 = deposit_amount.to_bytes(8, 'big')
    timestamp_bytes8 = int(w3.eth.getBlock(w3.eth.blockNumber)['timestamp']).to_bytes(8, 'big')
    assert log['previous_receipt_root'] == b'\x00' * 32
    assert log['data'] == amount_bytes8 + timestamp_bytes8 + deposit_input
    assert log['deposit_count'] == 0


def test_reciept_tree(registration_contract, w3, assert_tx_failed):
    deposit_amount = MAX_DEPOSIT * eth_utils.denoms.gwei
    amount_bytes8 = deposit_amount.to_bytes(8, 'big')

    leaf_nodes = []
    for i in range(1, 10):
        deposit_input = i.to_bytes(1, 'big') * 100
        tx_hash = registration_contract.functions.deposit(
            deposit_input,
        ).transact({"value": w3.toWei(deposit_amount, "gwei")})
        receipt = w3.eth.getTransactionReceipt(tx_hash)
        print("deposit transaction consumes %d gas" % receipt['gasUsed'])

        timestamp_bytes8 = int(w3.eth.getBlock(w3.eth.blockNumber)['timestamp']).to_bytes(8, 'big')
        data = amount_bytes8 + timestamp_bytes8 + deposit_input
        leaf_nodes.append(w3.sha3(data))
        root = compute_merkle_root(w3, leaf_nodes)
        assert registration_contract.functions.get_receipt_root().call() == root


def test_chain_start(modified_registration_contract, w3, assert_tx_failed):
    # CHAIN_START_FULL_DEPOSIT_THRESHOLD is adjusted to 5
    # First make 1 deposit with value below MAX_DEPOSIT
    min_deposit_amount = MIN_DEPOSIT * eth_utils.denoms.gwei  # in gwei
    deposit_input = b'\x01' * 100
    modified_registration_contract.functions.deposit(
        deposit_input,
    ).transact({"value": w3.toWei(min_deposit_amount, "gwei")})

    log_filter = modified_registration_contract.events.ChainStart.createFilter(
        fromBlock='latest',
    )

    max_deposit_amount = MAX_DEPOSIT * eth_utils.denoms.gwei
    # Next make 4 deposit with value MAX_DEPOSIT
    for i in range(2, 6):
        deposit_input = i.to_bytes(1, 'big') * 100
        modified_registration_contract.functions.deposit(
            deposit_input,
        ).transact({"value": w3.toWei(max_deposit_amount, "gwei")})
        logs = log_filter.get_new_entries()
        # ChainStart event should not be triggered
        assert len(logs) == 0

    # Make 1 more deposit with value MAX_DEPOSIT to trigger ChainStart event
    deposit_input = b'\x06' * 100
    modified_registration_contract.functions.deposit(
        deposit_input,
    ).transact({"value": w3.toWei(max_deposit_amount, "gwei")})
    logs = log_filter.get_new_entries()
    assert len(logs) == 1
