import pytest
from multidict import MultiDict, MultiDictProxy

from yarl import URL


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


def test_path_string_empty():
    url = URL('http://example.com')
    assert '/' == url.path


def test_path_empty():
    url = URL('http://example.com')
    assert ('/',) == url.parts


def test_path():
    url = URL('http://example.com/path/to')
    assert ('/', 'path', 'to') == url.parts


def test_path_string():
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


def test_query_string():
    url = URL('http://example.com?a=1&b=2')
    assert url.query_string == 'a=1&b=2'


def test_query_repeated_args():
    url = URL('http://example.com?a=1&b=2&a=3')
    assert url.query == MultiDict([('a', '1'), ('b', '2'), ('a', '3')])


def test_fragment_empty():
    url = URL('http://example.com')
    assert '' == url.fragment


def test_fragment():
    url = URL('http://example.com/path#anchor')
    assert 'anchor' == url.fragment


def test_parent_path_string():
    url = URL('http://example.com/path/to')
    assert url.parent.path == '/path'


def test_parent_path():
    url = URL('http://example.com/path/to')
    assert url.parent.parts == ('/', 'path')


def test_parent_double():
    url = URL('http://example.com/path/to')
    assert url.parent.parent.path == '/'


def test_parent_empty():
    url = URL('http://example.com/')
    assert url.parent.parent.path == '/'


def test_parent_empty2():
    url = URL('http://example.com')
    assert url.parent.parent.path == '/'


def test_ne_str():
    url = URL('http://example.com/')
    assert url != 'http://example.com/'


def test_eq():
    url = URL('http://example.com/')
    assert url == URL('http://example.com/')


def test_hash():
    assert hash(URL('http://example.com/')) == hash(URL('http://example.com/'))


def test_hash_double_call():
    url = URL('http://example.com/')
    assert hash(url) == hash(url)


def test_le_less():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url1 <= url2


def test_le_eq():
    url1 = URL('http://example.com/')
    url2 = URL('http://example.com/')

    assert url1 <= url2


def test_le_not_implemented():
    url = URL('http://example1.com/')

    assert url.__le__(123) is NotImplemented


def test_lt():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url1 < url2


def test_lt_not_implemented():
    url = URL('http://example1.com/')

    assert url.__lt__(123) is NotImplemented


def test_ge_more():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url2 >= url1


def test_ge_eq():
    url1 = URL('http://example.com/')
    url2 = URL('http://example.com/')

    assert url2 >= url1


def test_ge_not_implemented():
    url = URL('http://example1.com/')

    assert url.__ge__(123) is NotImplemented


def test_gt():
    url1 = URL('http://example1.com/')
    url2 = URL('http://example2.com/')

    assert url2 > url1


def test_gt_not_implemented():
    url = URL('http://example1.com/')

    assert url.__gt__(123) is NotImplemented


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


def test_div_root_with_slash():
    url = URL('http://example.com/')
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


def test_with_host_invalid_type():
    url = URL('http://example.com:123')
    with pytest.raises(TypeError):
        url.with_host(None)


def test_with_user():
    url = URL('http://example.com')
    assert str(url.with_user('john')) == 'http://john@example.com'


def test_with_user_invalid_type():
    url = URL('http://example.com:123')
    with pytest.raises(TypeError):
        url.with_user(None)


def test_with_password():
    url = URL('http://john@example.com')
    assert str(url.with_password('pass')) == 'http://john:pass@example.com'


def test_with_password_invalid_type():
    url = URL('http://example.com:123')
    with pytest.raises(TypeError):
        url.with_password(None)


def test_with_password_and_empty_user():
    url = URL('http://example.com')
    with pytest.raises(ValueError):
        assert str(url.with_password('pass'))


def test_with_scheme():
    url = URL('http://example.com')
    assert str(url.with_scheme('https')) == 'https://example.com'


def test_with_scheme_invalid_type():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        assert str(url.with_scheme(123))


def test_with_query():
    url = URL('http://example.com')
    assert str(url.with_query({'a': 1})) == 'http://example.com/?a=1'


def test_with_query_multidict():
    url = URL('http://example.com/path')
    q = MultiDict([('a', 'b'), ('c', 'd')])
    assert str(url.with_query(q)) == 'http://example.com/path?a=b&c=d'


def test_with_query_bad_type():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_query(None)


def test_with_fragment():
    url = URL('http://example.com')
    assert str(url.with_fragment('frag')) == 'http://example.com/#frag'


def test_with_fragment_bad_type():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_fragment(None)


def test_no_scheme():
    url = URL('example.com')
    assert url.host is None
    assert url.path == 'example.com'
    assert str(url) == 'example.com'


def test_no_scheme2():
    url = URL('example.com/a/b')
    assert url.host is None
    assert url.path == 'example.com/a/b'
    assert str(url) == 'example.com/a/b'


def test_from_bytes():
    url = URL(b'http://example.com')
    assert "http://example.com" == str(url)


def test_from_bytes_memoryview():
    url = URL(memoryview(b'http://example.com'))
    assert "http://example.com" == str(url)


def test_from_bytes_bytearray():
    url = URL(bytearray(b'http://example.com'))
    assert "http://example.com" == str(url)


def test_from_bytes_non_bytes():
    with pytest.raises(TypeError):
        URL(1234)


def test_from_bytes_idna():
    url = URL(b'http://xn--jxagkqfkduily1i.eu')
    assert "http://εμπορικόσήμα.eu" == str(url)


def test_from_bytes_with_non_ascii_login():
    url = URL(b'http://'
              b'%D0%B2%D0%B0%D1%81%D1%8F'
              b'@host:1234/')
    assert 'http://вася@host:1234/' == str(url)


def test_from_bytes_with_non_ascii_login_and_password():
    url = URL(b'http://'
              b'%D0%B2%D0%B0%D1%81%D1%8F'
              b':%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C'
              b'@host:1234/')
    assert 'http://вася:пароль@host:1234/' == str(url)


def test_from_bytes_with_non_ascii_path():
    url = URL(b'http://example.com/'
              b'%D0%BF%D1%83%D1%82%D1%8C/%D1%82%D1%83%D0%B4%D0%B0')
    assert 'http://example.com/путь/туда' == str(url)


def test_from_bytes_with_non_ascii_query_parts():
    url = URL(b'http://example.com/'
              b'?%D0%BF%D0%B0%D1%80%D0%B0%D0%BC'
              b'=%D0%B7%D0%BD%D0%B0%D1%87')
    assert 'http://example.com/?парам=знач' == str(url)


def test_from_bytes_with_non_ascii_fragment():
    url = URL(b'http://example.com/'
              b'#%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82')
    assert 'http://example.com/#фрагмент' == str(url)


def test_to_bytes():
    url = URL("http://εμπορικόσήμα.eu/")
    assert b"http://xn--jxagkqfkduily1i.eu/" == bytes(url)


def test_canonical():
    url = URL("http://εμπορικόσήμα.eu/")
    assert "http://xn--jxagkqfkduily1i.eu/" == url.canonical()


def test_to_bytes_long():
    url = URL('https://host-12345678901234567890123456789012345678901234567890'
              '-name:8888/')
    expected = (b'https://host-'
                b'12345678901234567890123456789012345678901234567890'
                b'-name:8888/')
    assert expected == bytes(url)


def test_to_bytes_with_login_and_password():
    url = URL('http://user:password@host:1234')
    assert b'http://user:password@host:1234' == bytes(url)


def test_to_bytes_with_non_ascii_login():
    url = URL('http://вася@host:1234')
    expected = (b'http://'
                b'%D0%B2%D0%B0%D1%81%D1%8F'
                b'@host:1234')
    assert expected == bytes(url)


def test_to_bytes_with_non_ascii_login_and_password():
    url = URL('http://вася:пароль@host:1234')
    expected = (b'http://'
                b'%D0%B2%D0%B0%D1%81%D1%8F'
                b':%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C'
                b'@host:1234')
    assert expected == bytes(url)


def test_to_bytes_with_non_ascii_path():
    url = URL('http://example.com/путь/туда')
    expected = (b'http://example.com/'
                b'%D0%BF%D1%83%D1%82%D1%8C/%D1%82%D1%83%D0%B4%D0%B0')
    assert expected == bytes(url)


def test_to_bytes_with_non_ascii_query_parts():
    url = URL('http://example.com/?парам=знач')
    expected = (b'http://example.com/'
                b'?%D0%BF%D0%B0%D1%80%D0%B0%D0%BC=%D0%B7%D0%BD%D0%B0%D1%87')
    assert expected == bytes(url)


def test_to_bytes_with_non_ascii_fragment():
    url = URL('http://example.com/#фрагмент')
    expected = (b'http://example.com/'
                b'#%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82')
    assert expected == bytes(url)


def test_decoding_with_2F_in_path():
    url = URL('http://example.com/path%2Fto')
    assert b'http://example.com/path%252Fto' == bytes(url)
    assert url == URL(bytes(url))


@pytest.mark.xfail
def test_decoding_with_26_and_3D_in_query():
    url = URL('http://example.com/?%26=%3D')
    assert b'http://example.com/?%2526=%253D' == bytes(url)
    assert url == URL(bytes(url))


def test_is_absolute_for_relative_url():
    url = URL('/path/to')
    assert not url.is_absolute()


def test_is_absolute_for_absolute_url():
    url = URL('http://example.com')
    assert url.is_absolute()


def test_not_allowed_query_only_url():
    with pytest.raises(ValueError):
        URL('?a=b')


def test_not_allowed_fragment_only_url():
    with pytest.raises(ValueError):
        URL('?a=b')


def test_not_allowed_empty():
    with pytest.raises(ValueError):
        URL('')


def test_relative_path():
    url = URL('path/to')
    assert ('path', 'to') == url.parts


def test_relative_path_starting_from_slash():
    url = URL('/path/to')
    assert ('/', 'path', 'to') == url.parts


def test_double_path():
    url = URL('path/to')
    assert url.parts == url.parts


def test_relative_name():
    url = URL('path/to')
    assert 'to' == url.name


def test_relative_name_starting_from_slash():
    url = URL('/path/to')
    assert 'to' == url.name


def test_relative_name_slash():
    url = URL('/')
    assert '' == url.name


def test_path_parts():
    url = URL('http://example.com/path/to/three')
    assert ('/', 'path', 'to', 'three') == url.parts


def test_parts_without_path():
    url = URL('http://example.com')
    assert ('/',) == url.parts


def test_path_parts_with_2F_in_path():
    url = URL('http://example.com/path%2Fto/three')
    assert ('/', 'path%2Fto', 'three') == url.parts


def test_path_parts_with_2f_in_path():
    url = URL('http://example.com/path%2fto/three')
    assert ('/', 'path%2fto', 'three') == url.parts


def test_url_from_url():
    url = URL('http://example.com')
    assert URL(url) is url
    assert URL(url).parts == ('/',)


def test_with_name():
    url = URL('http://example.com/a/b')
    assert url.parts == ('/', 'a', 'b')
    url2 = url.with_name('c')
    assert url2.parts == ('/', 'a', 'c')


def test_with_name_for_naked_path():
    url = URL('http://example.com')
    url2 = url.with_name('a')
    assert url2.parts == ('/', 'a')


def test_with_name_for_relative_path():
    url = URL('a')
    url2 = url.with_name('b')
    assert url2.parts == ('b',)


def test_with_name_for_relative_path2():
    url = URL('a/b')
    url2 = url.with_name('c')
    assert url2.parts == ('a', 'c')


def test_with_name_for_relative_path_starting_from_slash():
    url = URL('/a')
    url2 = url.with_name('b')
    assert url2.parts == ('/', 'b')


def test_with_name_for_relative_path_starting_from_slash2():
    url = URL('/a/b')
    url2 = url.with_name('c')
    assert url2.parts == ('/', 'a', 'c')


def test_with_name_empty():
    with pytest.raises(ValueError):
        URL('http://example.com').with_name('')


def test_with_name_with_slash():
    with pytest.raises(ValueError):
        URL('http://example.com').with_name('a/b')


def test_with_name_non_str():
    with pytest.raises(TypeError):
        URL('http://example.com').with_name(123)
