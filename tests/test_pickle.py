import pickle

from yarl import URL

# serialize


def test_pickle():
    u1 = URL("test")
    hash(u1)
    v = pickle.dumps(u1)
    u2 = pickle.loads(v)
    assert u1._cache
    assert hash(u1) == hash(u2)


def test_default_style_state():
    u = URL("test")
    hash(u)
    val = ("test", "test", "test", "test", "test")
    u.__setstate__((None, {"_val": val, "_strict": False, "_cache": {"hash": 1}}))
    assert u._val == val
