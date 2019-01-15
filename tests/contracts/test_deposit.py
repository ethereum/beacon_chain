from random import randint

import pytest

import eth_utils

from eth_hash.auto import keccak as hash

from tests.contracts.conftest import (
    MAX_DEPOSIT,
    MIN_DEPOSIT,
    DEPOSIT_CONTRACT_TREE_DEPTH,
    TWO_TO_POWER_OF_TREE_DEPTH,
)


def compute_merkle_root(leaf_nodes):
    assert len(leaf_nodes) >= 1
    empty_node = b'\x00' * 32
    child_nodes = leaf_nodes[:]
    for i in range(DEPOSIT_CONTRACT_TREE_DEPTH):
        parent_nodes = []
        if len(child_nodes) % 2 == 1:
            child_nodes.append(empty_node)
        for j in range(0, len(child_nodes), 2):
            parent_nodes.append(hash(child_nodes[j] + child_nodes[j+1]))
        child_nodes = parent_nodes
    return child_nodes[0]


def verify_merkle_branch(leaf, branch, depth, index, root):
    value = leaf
    for i in range(depth):
        if index // (2**i) % 2:
            value = hash(branch[i] + value)
        else:
            value = hash(value + branch[i])
    return value == root


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
    log_filter = registration_contract.events.Deposit.createFilter(
        fromBlock='latest',
    )

    deposit_amount = [randint(MIN_DEPOSIT, MAX_DEPOSIT) * eth_utils.denoms.gwei for _ in range(3)]
    for i in range(3):
        deposit_input = i.to_bytes(1, 'big') * 100
        registration_contract.functions.deposit(
            deposit_input,
        ).transact({"value": w3.toWei(deposit_amount[i], "gwei")})

        logs = log_filter.get_new_entries()
        assert len(logs) == 1
        log = logs[0]['args']

        amount_bytes8 = deposit_amount[i].to_bytes(8, 'big')
        timestamp_bytes8 = int(w3.eth.getBlock(w3.eth.blockNumber)['timestamp']).to_bytes(8, 'big')
        if i == 0:
            assert log['previous_deposit_root'] == b'\x00' * 32
        else:
            assert log['previous_deposit_root'] != b'\x00' * 32
        assert log['data'] == amount_bytes8 + timestamp_bytes8 + deposit_input
        assert log['merkle_tree_index'] == (i + TWO_TO_POWER_OF_TREE_DEPTH).to_bytes(8, 'big')


def test_receipt_tree(registration_contract, w3, assert_tx_failed):
    deposit_amount = [randint(MIN_DEPOSIT, MAX_DEPOSIT) * eth_utils.denoms.gwei for _ in range(10)]

    leaf_nodes = []
    for i in range(0, 10):
        deposit_input = i.to_bytes(1, 'big') * 100
        tx_hash = registration_contract.functions.deposit(
            deposit_input,
        ).transact({"value": w3.toWei(deposit_amount[i], "gwei")})
        receipt = w3.eth.getTransactionReceipt(tx_hash)
        print("deposit transaction consumes %d gas" % receipt['gasUsed'])

        timestamp_bytes8 = int(w3.eth.getBlock(w3.eth.blockNumber)['timestamp']).to_bytes(8, 'big')
        amount_bytes8 = deposit_amount[i].to_bytes(8, 'big')
        data = amount_bytes8 + timestamp_bytes8 + deposit_input
        leaf_nodes.append(w3.sha3(data))
        root = compute_merkle_root(leaf_nodes)
        assert registration_contract.functions.get_deposit_root().call() == root
        index = randint(0, i)
        branch = registration_contract.functions.get_branch(index).call()
        assert verify_merkle_branch(
            leaf_nodes[index],
            branch,
            DEPOSIT_CONTRACT_TREE_DEPTH,
            index,
            root
        )


def test_chain_start(modified_registration_contract, w3, assert_tx_failed):
    t = getattr(modified_registration_contract, 'chain_start_full_deposit_threshold')
    # CHAIN_START_FULL_DEPOSIT_THRESHOLD is set to t
    min_deposit_amount = MIN_DEPOSIT * eth_utils.denoms.gwei  # in gwei
    max_deposit_amount = MAX_DEPOSIT * eth_utils.denoms.gwei
    log_filter = modified_registration_contract.events.ChainStart.createFilter(
        fromBlock='latest',
    )

    index_not_full_deposit = randint(0, t-1)
    for i in range(t):
        if i == index_not_full_deposit:
            # Deposit with value below MAX_DEPOSIT
            deposit_input = b'\x01' * 100
            modified_registration_contract.functions.deposit(
                deposit_input,
            ).transact({"value": w3.toWei(min_deposit_amount, "gwei")})
            logs = log_filter.get_new_entries()
            # ChainStart event should not be triggered
            assert len(logs) == 0
        else:
            # Deposit with value MAX_DEPOSIT
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
    timestamp = int(w3.eth.getBlock(w3.eth.blockNumber)['timestamp'])
    timestamp_day_boundary = timestamp + (86400 - timestamp % 86400)
    log = logs[0]['args']
    assert log['deposit_root'] == modified_registration_contract.functions.get_deposit_root().call()
    assert int.from_bytes(log['time'], byteorder='big') == timestamp_day_boundary

    # Make 1 deposit with value MAX_DEPOSIT and check that ChainStart event is not triggered
    deposit_input = b'\x07' * 100
    modified_registration_contract.functions.deposit(
        deposit_input,
    ).transact({"value": w3.toWei(max_deposit_amount, "gwei")})
    logs = log_filter.get_new_entries()
    assert len(logs) == 0
