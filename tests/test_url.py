import sys
from urllib.parse import SplitResult
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


def test_origin():
    url = URL('http://user:password@example.com:8888/path/to?a=1&b=2')
    assert URL('http://example.com:8888') == url.origin()


def test_origin_not_absolute_url():
    url = URL('/path/to?a=1&b=2')
    with pytest.raises(ValueError):
        url.origin()


def test_origin_no_scheme():
    url = URL('//user:password@example.com:8888/path/to?a=1&b=2')
    with pytest.raises(ValueError):
        url.origin()


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


def test_path_root():
    url = URL('http://example.com/#frag')
    assert '' == url.name


def test_name_root2():
    url = URL('http://example.com')
    assert '' == url.name


def test_name_root3():
    url = URL('http://example.com/')
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


def test_with_scheme_uppercased():
    url = URL('http://example.com')
    assert str(url.with_scheme('HTTPS')) == 'https://example.com'


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


def test_from_non_allowed():
    with pytest.raises(TypeError):
        URL(1234)


def test_from_idna():
    url = URL('http://xn--jxagkqfkduily1i.eu')
    assert "http://xn--jxagkqfkduily1i.eu" == str(url)


def test_to_idna():
    url = URL('http://εμπορικόσήμα.eu')
    assert "http://xn--jxagkqfkduily1i.eu" == str(url)


def test_from_ascii_login():
    url = URL('http://'
              '%D0%B2%D0%B0%D1%81%D1%8F'
              '@host:1234/')
    assert ('http://'
            '%D0%B2%D0%B0%D1%81%D1%8F'
            '@host:1234/') == str(url)


def test_from_non_ascii_login():
    url = URL('http://вася@host:1234/')
    assert ('http://'
            '%D0%B2%D0%B0%D1%81%D1%8F'
            '@host:1234/') == str(url)


def test_from_ascii_login_and_password():
    url = URL('http://'
              '%D0%B2%D0%B0%D1%81%D1%8F'
              ':%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C'
              '@host:1234/')
    assert ('http://'
            '%D0%B2%D0%B0%D1%81%D1%8F'
            ':%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C'
            '@host:1234/') == str(url)


def test_from_non_ascii_login_and_password():
    url = URL('http://вася:пароль@host:1234/')
    assert ('http://'
            '%D0%B2%D0%B0%D1%81%D1%8F'
            ':%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C'
            '@host:1234/') == str(url)


def test_from_ascii_path():
    url = URL('http://example.com/'
              '%D0%BF%D1%83%D1%82%D1%8C/%D1%82%D1%83%D0%B4%D0%B0')
    assert ('http://example.com/'
            '%D0%BF%D1%83%D1%82%D1%8C/%D1%82%D1%83%D0%B4%D0%B0') == str(url)


def test_from_ascii_path_lower_case():
    url = URL('http://example.com/'
              '%d0%bf%d1%83%d1%82%d1%8c/%d1%82%d1%83%d0%b4%d0%b0')
    assert ('http://example.com/'
            '%D0%BF%D1%83%D1%82%D1%8C/%D1%82%D1%83%D0%B4%D0%B0') == str(url)


def test_from_non_ascii_path():
    url = URL('http://example.com/путь/туда')
    assert ('http://example.com/'
            '%D0%BF%D1%83%D1%82%D1%8C/%D1%82%D1%83%D0%B4%D0%B0') == str(url)


def test_from_ascii_query_parts():
    url = URL('http://example.com/'
              '?%D0%BF%D0%B0%D1%80%D0%B0%D0%BC'
              '=%D0%B7%D0%BD%D0%B0%D1%87')
    assert ('http://example.com/'
            '?%D0%BF%D0%B0%D1%80%D0%B0%D0%BC'
            '=%D0%B7%D0%BD%D0%B0%D1%87') == str(url)


def test_from_non_ascii_query_parts():
    url = URL('http://example.com/?парам=знач')
    assert ('http://example.com/'
            '?%D0%BF%D0%B0%D1%80%D0%B0%D0%BC'
            '=%D0%B7%D0%BD%D0%B0%D1%87') == str(url)


def test_from_non_ascii_query_parts2():
    url = URL('http://example.com/?п=з&ю=б')
    assert 'http://example.com/?%D0%BF=%D0%B7&%D1%8E=%D0%B1' == str(url)


def test_from_ascii_fragment():
    url = URL('http://example.com/'
              '#%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82')
    assert ('http://example.com/'
            '#%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82') == str(url)


def test_from_bytes_with_non_ascii_fragment():
    url = URL('http://example.com/#фрагмент')
    assert ('http://example.com/'
            '#%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82') == str(url)


def test_to_str():
    url = URL("http://εμπορικόσήμα.eu/")
    assert "http://xn--jxagkqfkduily1i.eu/" == str(url)


def test_to_str_long():
    url = URL('https://host-12345678901234567890123456789012345678901234567890'
              '-name:8888/')
    expected = ('https://host-'
                '12345678901234567890123456789012345678901234567890'
                '-name:8888/')
    assert expected == str(url)


def test_decoding_with_2F_in_path():
    url = URL('http://example.com/path%2Fto')
    assert 'http://example.com/path%2Fto' == str(url)
    assert url == URL(str(url))


def test_decoding_with_26_and_3D_in_query():
    url = URL('http://example.com/?%26=%3D')
    assert 'http://example.com/?%26=%3D' == str(url)
    assert url == URL(str(url))


def test_is_absolute_for_relative_url():
    url = URL('/path/to')
    assert not url.is_absolute()


def test_is_absolute_for_absolute_url():
    url = URL('http://example.com')
    assert url.is_absolute()


def test_fragment_only_url():
    url = URL('#frag')
    assert str(url) == "#frag"


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
    assert ('/', 'path%2Fto', 'three') == url.parts


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


def test_lowercase_scheme():
    url = URL('HTTP://example.com')
    assert str(url) == 'http://example.com'


def test_is_non_absolute_for_empty_url():
    url = URL()
    assert not url.is_absolute()


def test_is_non_absolute_for_empty_url2():
    url = URL('')
    assert not url.is_absolute()


def test_parts_for_empty_url():
    url = URL()
    assert ('',) == url.parts


def test_name_for_empty_url():
    url = URL()
    assert '' == url.name


def test_path_for_empty_url():
    url = URL()
    assert '' == url.path


def test_str_for_empty_url():
    url = URL()
    assert '' == str(url)


def test_parent_for_empty_url():
    url = URL()
    assert url is url.parent


def test_truediv_for_empty_url():
    url = URL() / 'a'
    assert url.parts == ('a',)


def test_truediv_for_relative_url():
    url = URL('a') / 'b'
    assert url.parts == ('a', 'b')


def test_truediv_for_relative_url_started_with_slash():
    url = URL('/a') / 'b'
    assert url.parts == ('/', 'a', 'b')


def test_empty_value_for_query():
    url = URL('http://example.com/path').with_query({'a': ''})
    assert str(url) == 'http://example.com/path?a='


@pytest.mark.xfail
def test_none_value_for_query():
    url = URL('http://example.com/path').with_query({'a': None})
    assert str(url) == 'http://example.com/path?a'


def test_is_absolute_path_starting_from_double_slash():
    url = URL('//www.python.org')
    assert url.is_absolute()


def test_decode_pct_in_path():
    url = URL('http://www.python.org/%7Eguido')
    assert 'http://www.python.org/~guido' == str(url)


def test_decode_pct_in_path_lower_case():
    url = URL('http://www.python.org/%7eguido')
    assert 'http://www.python.org/~guido' == str(url)


def test_join():
    base = URL('http://www.cwi.nl/%7Eguido/Python.html')
    url = URL('FAQ.html')
    url2 = base.join(url)
    assert str(url2) == 'http://www.cwi.nl/~guido/FAQ.html'


def test_join_absolute():
    base = URL('http://www.cwi.nl/%7Eguido/Python.html')
    url = URL('//www.python.org/%7Eguido')
    url2 = base.join(url)
    assert str(url2) == 'http://www.python.org/~guido'


def test_join_non_url():
    base = URL('http://example.com')
    with pytest.raises(TypeError):
        base.join('path/to')


NORMAL = [
    ("g:h", "g:h"),
    ("g", "http://a/b/c/g"),
    ("./g", "http://a/b/c/g"),
    ("g/", "http://a/b/c/g/"),
    ("/g", "http://a/g"),
    ("//g", "http://g"),
    ("?y", "http://a/b/c/d;p?y"),
    ("g?y", "http://a/b/c/g?y"),
    ("#s", "http://a/b/c/d;p?q#s"),
    ("g#s", "http://a/b/c/g#s"),
    ("g?y#s", "http://a/b/c/g?y#s"),
    (";x", "http://a/b/c/;x"),
    ("g;x", "http://a/b/c/g;x"),
    ("g;x?y#s", "http://a/b/c/g;x?y#s"),
    ("", "http://a/b/c/d;p?q"),
    (".", "http://a/b/c/"),
    ("./", "http://a/b/c/"),
    ("..", "http://a/b/"),
    ("../", "http://a/b/"),
    ("../g", "http://a/b/g"),
    ("../..", "http://a/"),
    ("../../", "http://a/"),
    ("../../g", "http://a/g")
]


@pytest.mark.parametrize('url,expected', NORMAL)
def test_join_from_rfc_3986_normal(url, expected):
    # test case from https://tools.ietf.org/html/rfc3986.html#section-5.4
    base = URL('http://a/b/c/d;p?q')
    url = URL(url)
    expected = URL(expected)
    assert base.join(url) == expected


ABNORMAL = [
    ("../../../g", "http://a/g"),
    ("../../../../g", "http://a/g"),

    ("/./g", "http://a/g"),
    ("/../g", "http://a/g"),
    ("g.", "http://a/b/c/g."),
    (".g", "http://a/b/c/.g"),
    ("g..", "http://a/b/c/g.."),
    ("..g", "http://a/b/c/..g"),

    ("./../g", "http://a/b/g"),
    ("./g/.", "http://a/b/c/g/"),
    ("g/./h", "http://a/b/c/g/h"),
    ("g/../h", "http://a/b/c/h"),
    ("g;x=1/./y", "http://a/b/c/g;x=1/y"),
    ("g;x=1/../y", "http://a/b/c/y"),

    ("g?y/./x", "http://a/b/c/g?y/./x"),
    ("g?y/../x", "http://a/b/c/g?y/../x"),
    ("g#s/./x", "http://a/b/c/g#s/./x"),
    ("g#s/../x", "http://a/b/c/g#s/../x"),
]


@pytest.mark.skipif(sys.version_info < (3, 5),
                    reason="Python 3.4 doen't support abnormal cases")
@pytest.mark.parametrize('url,expected', ABNORMAL)
def test_join_from_rfc_3986_abnormal(url, expected):
    # test case from https://tools.ietf.org/html/rfc3986.html#section-5.4.2
    base = URL('http://a/b/c/d;p?q')
    url = URL(url)
    expected = URL(expected)
    assert base.join(url) == expected


def test_from_str_with_ipv4():
    url = URL('http://127.0.0.1:80')
    assert url.host == '127.0.0.1'


def test_from_str_with_ipv6():
    url = URL('http://[::1]:80')
    assert url.host == '::1'


def test_from_str_with_host_ipv4():
    url = URL('http://host:80')
    url = url.with_host('192.168.1.1')
    assert url.host == '192.168.1.1'


def test_from_str_with_host_ipv6():
    url = URL('http://host:80')
    url = url.with_host('::1')
    assert url.host == '::1'


def test_with_scheme_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_scheme('http')


def test_with_user_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_user('user')


def test_with_password_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_password('pass')


def test_with_host_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_host('example.com')


def test_with_port_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_port(1234)


def test_split_result_non_decoded():
    with pytest.raises(ValueError):
        URL(SplitResult('http', 'example.com', 'path', 'qs', 'frag'))
