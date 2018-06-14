try:
    from hashlib import blake2s
except:
    from pyblake2 import blake2s


def blake(x):
    return blake2s(x).digest()
