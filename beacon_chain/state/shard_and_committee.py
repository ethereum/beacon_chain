class ShardAndCommittee():
    fields = {
        # The shard ID
        'shard_id': 'int16',
        # Validator indices
        'committee': ['int24'],
    }

    defaults = {
        'shard_id': 0,
        'committee': [],
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
