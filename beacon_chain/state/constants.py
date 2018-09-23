from eth_utils import denoms

from beacon_chain.beacon_typing.custom import (
    Hash32,
)


WEI_PER_ETH = denoms.ether
ZERO_HASH32 = Hash32(32 * b'\x00')
