import pytest

from urllib.parse import urlencode

from multidict import MultiDict, MultiDictProxy


from yarl import URL

# query


def test_query_spaces():
    url = URL('http://example.com?a+b=c+d')
    assert url.query == MultiDict({'a b': 'c d'})


def test_query_empty():
    url = URL('http://example.com')
    assert isinstance(url.query, MultiDictProxy)
    assert url.query == MultiDict()


def test_query():
    url = URL('http://example.com?a=1&b=2')
    assert url.query == MultiDict([('a', '1'), ('b', '2')])


def test_query_repeated_args():
    url = URL('http://example.com?a=1&b=2&a=3')
    assert url.query == MultiDict([('a', '1'), ('b', '2'), ('a', '3')])


def test_query_empty_arg():
    url = URL('http://example.com?a')
    assert url.query == MultiDict([('a', '')])


def test_query_dont_unqoute_twice():
    sample_url = 'http://base.place?' + urlencode({'a': '/////'})
    query = urlencode({'url': sample_url})
    full_url = 'http://test_url.aha?' + query

    url = URL(full_url)
    assert url.query['url'] == sample_url


def test_query_nonascii():
    url = URL('http://example.com?ключ=знач')
    assert url.query == MultiDict({'ключ': 'знач'})


# query separators

def test_ampersand_as_separator():
    u = URL('http://127.0.0.1/?a=1&b=2')
    assert len(u.query) == 2


def test_ampersand_as_value():
    u = URL('http://127.0.0.1/?a=1%26b=2')
    assert len(u.query) == 1
    assert u.query['a'] == '1&b=2'


def test_semicolon_as_separator():
    u = URL('http://127.0.0.1/?a=1;b=2')
    assert len(u.query) == 2


def test_semicolon_as_value():
    u = URL('http://127.0.0.1/?a=1%3Bb=2')
    assert len(u.query) == 1
    assert u.query['a'] == '1;b=2'


@pytest.mark.xfail
# FIXME: Converting a well-encoded URL with embedded URL should return a
# well-encoded URL again.
def test_embedded_url():
    original_url_str = (
        "https://example.com/something?"
        "embedded=http%3A%2F%2Ftarget.test%2Fan%2520action%3F"
        "foo%2520bar%3Dabc%2Bdef%23a%2520fragment"
        "#pointing"
    )
    u = URL(original_url_str)

    assert len(u.query) == 1
    assert u.query['embedded'] == (
        'http://target.test/an%20action?'
        'foo%20bar=abc+def#a%20fragment'
    )
    assert str(u) == original_url_str
