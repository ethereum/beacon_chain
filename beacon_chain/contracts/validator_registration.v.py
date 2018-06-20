Deposit: event({
    pubkey: bytes32,
    withdrawal_shard_id: uint256,
    withdrawal_addr: address,
    randao_commitment: bytes32})


validators: public(bool[address])


@public
@payable
def deposit(
        pubkey: bytes32,
        withdrawal_shard_id: uint256,
        withdrawal_addr: address,
        randao_commitment: bytes32):
    assert msg.value == as_wei_value(32, "ether")
    assert not self.validators[pubkey]

    self.validators[pubkey] = True

    log.Deposit(pubkey, withdrawal_shard_id,
                withdrawal_addr, randao_commitment)
