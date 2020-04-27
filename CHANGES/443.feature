These changes fix https://github.com/aio-libs/aiohttp/issues/4714, that is,
we now support the use of lists and tuples when quoting mappings such as
Python's builtin dict. As an example from the tests:

    url = URL("http://example.com")
    assert url.with_query({"a": [1, 2]}) == URL("http://example.com/?a=1&a=2")
