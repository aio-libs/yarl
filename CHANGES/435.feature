Allow to use mod operator (`%`) for updating query string:

    url = URL("http://example.com")
    assert url % {"a": "1"} == URL("http://example.com?a=1")