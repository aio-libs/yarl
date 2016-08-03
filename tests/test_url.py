import pytest
from yarl import URL
from multidict import MultiDict, MultiDictProxy


def test_url_is_not_str():
    url = URL('http://example.com')
    assert not isinstance(url, str)


def test_str():
    url = URL('http://example.com:8888/path/to?a=1&b=2')
    assert str(url) == 'http://example.com:8888/path/to?a=1&b=2'


def test_repr():
    url = URL('http://example.com')
    assert "URL('http://example.com')" == repr(url)


def test_host():
    url = URL('http://example.com')
    assert "example.com" == url.host


def test_host_when_port_is_specified():
    url = URL('http://example.com:8888')
    assert "example.com" == url.host


def test_explicit_port():
    url = URL('http://example.com:8888')
    assert 8888 == url.port


def test_implicit_port():
    url = URL('http://example.com')
    assert 80 == url.port


def test_port_for_unknown_scheme():
    url = URL('unknown://example.com')
    assert url.port is None


def test_scheme():
    url = URL('http://example.com')
    assert 'http' == url.scheme


def test_path_empty():
    url = URL('http://example.com')
    assert '/' == url.path


def test_path():
    url = URL('http://example.com/path/to')
    assert '/path/to' == url.path


def test_user():
    url = URL('http://user@example.com')
    assert 'user' == url.user


def test_password():
    url = URL('http://user:password@example.com')
    assert 'password' == url.password


def test_empty_query():
    url = URL('http://example.com')
    assert isinstance(url.query, MultiDictProxy)
    assert url.query == MultiDict()


def test_query():
    url = URL('http://example.com?a=1&b=2')
    assert url.query == MultiDict([('a', '1'), ('b', '2')])


def test_query_repeated_args():
    url = URL('http://example.com?a=1&b=2&a=3')
    assert url.query == MultiDict([('a', '1'), ('b', '2'), ('a', '3')])


def test_fragment_empty():
    url = URL('http://example.com')
    assert '' == url.fragment


def test_fragment():
    url = URL('http://example.com/path#anchor')
    assert 'anchor' == url.fragment


def test_parent():
    url = URL('http://example.com/path/to')
    assert url.parent.path == '/path'


def test_parent_double():
    url = URL('http://example.com/path/to')
    assert url.parent.parent.path == '/'


def test_parent_empty():
    url = URL('http://example.com/')
    assert url.parent.parent.path == '/'


def test_ne_str():
    url = URL('http://example.com/')
    assert url != 'http://example.com/'


def test_eq():
    url = URL('http://example.com/')
    assert url == URL('http://example.com/')


def test_hash():
    assert hash(URL('http://example.com/')) == hash(URL('http://example.com/'))


def test_le_less():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url1 <= url2


def test_le_eq():
    url1 = URL('http://example.com/')
    url2 = URL('http://example.com/')

    assert url1 <= url2


def test_lt():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url1 < url2


def test_ge_more():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url2 >= url1


def test_ge_eq():
    url1 = URL('http://example.com/')
    url2 = URL('http://example.com/')

    assert url2 >= url1


def test_gt():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url2 > url1


def test_clear_fragment_on_getting_parent():
    url = URL('http://example.com/path/to#frag')
    assert URL('http://example.com/path') == url.parent


def test_clear_fragment_on_getting_parent_toplevel():
    url = URL('http://example.com/#frag')
    assert URL('http://example.com/') == url.parent


def test_clear_query_on_getting_parent():
    url = URL('http://example.com/path/to?a=b')
    assert URL('http://example.com/path') == url.parent


def test_clear_query_on_getting_parent_toplevel():
    url = URL('http://example.com/?a=b')
    assert URL('http://example.com/') == url.parent


def test_name():
    url = URL('http://example.com/path/to#frag')
    assert 'to' == url.name


def test_name_root():
    url = URL('http://example.com/#frag')
    assert '' == url.name


def test_name_root2():
    url = URL('http://example.com')
    assert '' == url.name


def test_div_root():
    url = URL('http://example.com')
    assert str(url / 'path' / 'to') == 'http://example.com/path/to'


def test_div():
    url = URL('http://example.com/path')
    assert str(url / 'to') == 'http://example.com/path/to'


def test_div_cleanup_query_and_fragment():
    url = URL('http://example.com/path?a=1#frag')
    assert str(url / 'to') == 'http://example.com/path/to'


def test_with_port():
    url = URL('http://example.com')
    assert str(url.with_port(8888)) == 'http://example.com:8888'


def test_with_port_keeps_query_and_fragment():
    url = URL('http://example.com/?a=1#frag')
    assert str(url.with_port(8888)) == 'http://example.com:8888/?a=1#frag'


def test_with_port_invalid_type():
    with pytest.raises(TypeError):
        URL('http://example.com').with_port('123')


def test_with_host():
    url = URL('http://example.com:123')
    assert str(url.with_host('example.org')) == 'http://example.org:123'


def test_with_user():
    url = URL('http://example.com')
    assert str(url.with_user('john')) == 'http://john@example.com'


def test_with_password():
    url = URL('http://john@example.com')
    assert str(url.with_password('pass')) == 'http://john:pass@example.com'


def test_with_password_and_empty_user():
    url = URL('http://example.com')
    with pytest.raises(ValueError):
        assert str(url.with_password('pass'))


def test_with_scheme():
    url = URL('http://example.com')
    assert str(url.with_scheme('https')) == 'https://example.com'


def test_with_path():
    url = URL('http://example.com/p1/p2')
    assert str(url.with_path('/p3/p4')) == 'http://example.com/p3/p4'


def test_with_query():
    url = URL('http://example.com')
    assert str(url.with_query({'a': 1})) == 'http://example.com?a=1'


def test_with_query_multidict():
    url = URL('http://example.com')
    q = MultiDict([('a', 'b'), ('c', 'd')])
    assert str(url.with_query(q)) == 'http://example.com?a=b&c=d'


def test_with_fragment():
    url = URL('http://example.com')
    assert str(url.with_fragment('frag')) == 'http://example.com#frag'
