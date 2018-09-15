try:
    from hashlib import blake2b
except Exception:
    from pyblake2 import blake2b


def blake(x):
    return blake2b(x).digest()[:32]
