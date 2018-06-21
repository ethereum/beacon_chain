Deposit: event({
    pubkey: bytes32,
    withdrawal_shard_id: uint256,
    withdrawal_addr: address,
    randao_commitment: bytes32})


used_pubkey: public(bool[bytes32])


@public
@payable
def deposit(
        pubkey: bytes32,
        withdrawal_shard_id: uint256,
        withdrawal_address: address,
        randao_commitment: bytes32):
    assert msg.value == as_wei_value(32, "ether")
    assert not self.used_pubkey[pubkey]

    self.used_pubkey[pubkey] = True

    log.Deposit(pubkey, withdrawal_shard_id,
                withdrawal_address, randao_commitment)
