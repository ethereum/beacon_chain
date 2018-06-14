
class CheckpointRecord():

    fields = {
        # What shard is the crosslink being made for
        'shard_id': 'int16',
        # Hash of the block
        'checkpoint_hash': 'hash32',
        # Which of the eligible voters are voting for it (as a bitmask)
        'voter_bitmask': 'bytes'
    }
    defaults = {}

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults, k
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
