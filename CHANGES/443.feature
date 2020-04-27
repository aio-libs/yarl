Allow use of sequences such as :class:`list` and :class:`tuple` in the values
of a mapping such as :class:`dict` to represent that a key has many values:

    url = URL("http://example.com")
    assert url.with_query({"a": [1, 2]}) == URL("http://example.com/?a=1&a=2")
