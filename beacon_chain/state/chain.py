
class Chain():
    # Note, this is not an object defined in the v2.1 spec
    # this is a helper object to mask complexity in tracking
    # blocks

    def __init__(self, head=None, blocks=[]):
        self.head = head
        self.blocks = blocks
        self.block_by_hash = {
            block.hash: block
            for block in self.blocks
        }
        self.chain = []

        if self.head:
            tmp = self.head
            self.chain.append(tmp)
            while self.block_by_hash.get(tmp.parent_hash, None):
                tmp = self.block_by_hash[tmp.parent_hash]
                self.chain.append(tmp)

        self.block_by_slot_number = {
            block.slot_number: block
            for block in self.chain
        }

    def get_block_by_slot_number(self, slot_number):
        return self.block_by_slot_number.get(slot_number, None)
