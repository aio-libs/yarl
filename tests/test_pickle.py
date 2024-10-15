import pickle

from yarl import URL

# serialize


def test_pickle():
    u1 = URL("test")
    hash(u1)
    v = pickle.dumps(u1)
    u2 = pickle.loads(v)
    assert hash(u1) == hash(u2)


def test_default_style_state():
    u = URL("test")
    hash(u)
    u.__setstate__((None, {"_val": "test", "_strict": False}))
    assert u._val == "test"
