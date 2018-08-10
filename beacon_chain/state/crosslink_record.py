
class CrosslinkRecord():
    fields = {
        # What dynasty the crosslink was submitted in
        'dynasty': 'int64',
        # The block hash
        'hash': 'hash32'
    }
    defaults = {
        'dynasty': 0,
        'hash': b'\x00'*32
    }

    def __init__(self, **kwargs):
        for k in self.fields.keys():
            assert k in kwargs or k in self.defaults
            setattr(self, k, kwargs.get(k, self.defaults.get(k)))
