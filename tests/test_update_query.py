import pytest

from multidict import MultiDict


from yarl import URL


# with_query

def test_with_query():
    url = URL('http://example.com')
    assert str(url.with_query({'a': '1'})) == 'http://example.com/?a=1'


def test_update_query():
    url = URL('http://example.com/')
    assert str(url.update_query({'a': '1'})) == 'http://example.com/?a=1'
    assert str(URL('test').update_query(a=1)) == 'test?a=1'

    url = URL('http://example.com/?foo=bar')
    expected_url = URL('http://example.com/?foo=bar&baz=foo')

    assert url.update_query({'baz': 'foo'}) == expected_url
    assert url.update_query(baz='foo') == expected_url
    assert url.update_query("?baz=foo") == expected_url


def test_update_query_with_args_and_kwargs():
    url = URL('http://example.com/')

    with pytest.raises(ValueError):
        url.update_query('a', foo='bar')


def test_update_query_with_multiple_args():
    url = URL('http://example.com/')

    with pytest.raises(ValueError):
        url.update_query('a', 'b')


def test_with_query_list_of_pairs():
    url = URL('http://example.com')
    assert str(url.with_query([('a', '1')])) == 'http://example.com/?a=1'


def test_with_query_kwargs():
    url = URL('http://example.com')
    q = url.with_query(query='1', query2='1').query
    assert q == dict(query='1', query2='1')


def test_with_query_kwargs_and_args_are_mutually_exclusive():
    url = URL('http://example.com')
    with pytest.raises(ValueError):
        url.with_query(
            {'a': '2', 'b': '4'}, a='1')


def test_with_query_only_single_arg_is_supported():
    url = URL('http://example.com')
    u1 = url.with_query(b=3)
    u2 = URL('http://example.com/?b=3')
    assert u1 == u2
    with pytest.raises(ValueError):
        url.with_query('a=1', 'a=b')


def test_with_query_empty_dict():
    url = URL('http://example.com/?a=b')
    assert str(url.with_query({})) == 'http://example.com/'


def test_with_query_empty_str():
    url = URL('http://example.com/?a=b')
    assert str(url.with_query('')) == 'http://example.com/'


def test_with_query_str():
    url = URL('http://example.com')
    assert str(url.with_query('a=1&b=2')) == 'http://example.com/?a=1&b=2'


def test_with_query_str_non_ascii_and_spaces():
    url = URL('http://example.com')
    url2 = url.with_query('a=1 2&b=знач')
    assert url2.raw_query_string == 'a=1+2&b=%D0%B7%D0%BD%D0%B0%D1%87'
    assert url2.query_string == 'a=1 2&b=знач'


def test_with_query_int():
    url = URL('http://example.com')
    assert url.with_query({'a': 1}) == URL('http://example.com/?a=1')


def test_with_query_non_str():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_query({'a': 1.1})


def test_with_query_multidict():
    url = URL('http://example.com/path')
    q = MultiDict([('a', 'b'), ('c', 'd')])
    assert str(url.with_query(q)) == 'http://example.com/path?a=b&c=d'


def test_with_multidict_with_spaces_and_non_ascii():
    url = URL('http://example.com')
    url2 = url.with_query({'a b': 'ю б'})
    assert url2.raw_query_string == 'a+b=%D1%8E+%D0%B1'


def test_with_query_multidict_with_unsafe():
    url = URL('http://example.com/path')
    url2 = url.with_query({'a+b': '?=+&;'})
    assert url2.raw_query_string == 'a%2Bb=?%3D%2B%26%3B'
    assert url2.query_string == 'a%2Bb=?%3D%2B%26%3B'
    assert url2.query == {'a+b': '?=+&;'}


def test_with_query_None():
    url = URL('http://example.com/path?a=b')
    assert url.with_query(None).query_string == ''


def test_with_query_bad_type():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_query(123)


def test_with_query_bytes():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_query(b'123')


def test_with_query_bytearray():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_query(bytearray(b'123'))


def test_with_query_memoryview():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_query(memoryview(b'123'))


def test_with_query_params():
    url = URL('http://example.com/get')
    url2 = url.with_query([('key', '1;2;3')])
    assert str(url2) == 'http://example.com/get?key=1%3B2%3B3'


def test_with_query_params2():
    url = URL('http://example.com/get')
    url2 = url.with_query({'key': '1;2;3'})
    assert str(url2) == 'http://example.com/get?key=1%3B2%3B3'


def test_with_query_only():
    url = URL()
    url2 = url.with_query(key='value')
    assert str(url2) == '?key=value'
