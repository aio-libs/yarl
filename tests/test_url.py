import sys
import pytest
from urllib.parse import SplitResult

from yarl import URL


def test_absolute_url_without_host():
    with pytest.raises(ValueError):
        URL('http://:8080/')


def test_url_is_not_str():
    url = URL('http://example.com')
    assert not isinstance(url, str)


def test_str():
    url = URL('http://example.com:8888/path/to?a=1&b=2')
    assert str(url) == 'http://example.com:8888/path/to?a=1&b=2'


def test_repr():
    url = URL('http://example.com')
    assert "URL('http://example.com')" == repr(url)


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


def test_drop_dots():
    u = URL('http://example.com/path/../to')
    assert str(u) == 'http://example.com/to'


def test_abs_cmp():
    assert URL('http://example.com:8888') == URL('http://example.com:8888')
    assert URL('http://example.com:8888/') == URL('http://example.com:8888/')
    assert URL('http://example.com:8888/') == URL('http://example.com:8888')
    assert URL('http://example.com:8888') == URL('http://example.com:8888/')


def test_abs_hash():
    url = URL('http://example.com:8888')
    url_trailing = URL('http://example.com:8888/')
    assert hash(url) == hash(url_trailing)

# properties


def test_scheme():
    url = URL('http://example.com')
    assert 'http' == url.scheme


def test_raw_user():
    url = URL('http://user@example.com')
    assert 'user' == url.raw_user


def test_raw_user_non_ascii():
    url = URL('http://вася@example.com')
    assert '%D0%B2%D0%B0%D1%81%D1%8F' == url.raw_user


def test_no_user():
    url = URL('http://example.com')
    assert url.user is None


def test_user_non_ascii():
    url = URL('http://вася@example.com')
    assert 'вася' == url.user


def test_raw_password():
    url = URL('http://user:password@example.com')
    assert 'password' == url.raw_password


def test_raw_password_non_ascii():
    url = URL('http://user:пароль@example.com')
    assert '%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C' == url.raw_password


def test_password_non_ascii():
    url = URL('http://user:пароль@example.com')
    assert 'пароль' == url.password


def test_password_without_user():
    url = URL('http://:password@example.com')
    assert 'password' == url.password


def test_raw_host():
    url = URL('http://example.com')
    assert "example.com" == url.raw_host


def test_raw_host_non_ascii():
    url = URL('http://историк.рф')
    assert "xn--h1aagokeh.xn--p1ai" == url.raw_host


def test_host_non_ascii():
    url = URL('http://историк.рф')
    assert "историк.рф" == url.host


def test_raw_host_when_port_is_specified():
    url = URL('http://example.com:8888')
    assert "example.com" == url.raw_host


def test_raw_host_from_str_with_ipv4():
    url = URL('http://127.0.0.1:80')
    assert url.raw_host == '127.0.0.1'


def test_raw_host_from_str_with_ipv6():
    url = URL('http://[::1]:80')
    assert url.raw_host == '::1'


def test_explicit_port():
    url = URL('http://example.com:8888')
    assert 8888 == url.port


def test_implicit_port():
    url = URL('http://example.com')
    assert 80 == url.port


def test_port_for_relative_url():
    url = URL('/path/to')
    assert url.port is None


def test_port_for_unknown_scheme():
    url = URL('unknown://example.com')
    assert url.port is None


def test_raw_path_string_empty():
    url = URL('http://example.com')
    assert '/' == url.raw_path


def test_raw_path():
    url = URL('http://example.com/path/to')
    assert '/path/to' == url.raw_path


def test_raw_path_non_ascii():
    url = URL('http://example.com/путь/сюда')
    assert '/%D0%BF%D1%83%D1%82%D1%8C/%D1%81%D1%8E%D0%B4%D0%B0' == url.raw_path


def test_path_non_ascii():
    url = URL('http://example.com/путь/сюда')
    assert '/путь/сюда' == url.path


def test_path_with_spaces():
    url = URL('http://example.com/a b/test')
    assert '/a b/test' == url.path

    url = URL('http://example.com/a b')
    assert '/a b' == url.path


def test_raw_path_for_empty_url():
    url = URL()
    assert '' == url.raw_path


def test_raw_path_for_colon_and_at():
    url = URL('http://example.com/path:abc@123')
    assert url.raw_path == '/path:abc@123'


def test_raw_query_string():
    url = URL('http://example.com?a=1&b=2')
    assert url.raw_query_string == 'a=1&b=2'


def test_raw_query_string_non_ascii():
    url = URL('http://example.com?б=в&ю=к')
    assert url.raw_query_string == '%D0%B1=%D0%B2&%D1%8E=%D0%BA'


def test_query_string_non_ascii():
    url = URL('http://example.com?б=в&ю=к')
    assert url.query_string == 'б=в&ю=к'


def test_path_qs():
    url = URL('http://example.com/')
    assert url.path_qs == '/'
    url = URL('http://example.com/?б=в&ю=к')
    assert url.path_qs == '/?б=в&ю=к'
    url = URL('http://example.com/path?б=в&ю=к')
    assert url.path_qs == '/path?б=в&ю=к'


def test_query_string_spaces():
    url = URL('http://example.com?a+b=c+d&e=f+g')
    assert url.query_string == 'a b=c d&e=f g'

# raw fragment


def test_raw_fragment_empty():
    url = URL('http://example.com')
    assert '' == url.raw_fragment


def test_raw_fragment():
    url = URL('http://example.com/path#anchor')
    assert 'anchor' == url.raw_fragment


def test_raw_fragment_non_ascii():
    url = URL('http://example.com/path#якорь')
    assert '%D1%8F%D0%BA%D0%BE%D1%80%D1%8C' == url.raw_fragment


def test_raw_fragment_safe():
    url = URL('http://example.com/path#a?b/c:d@e')
    assert 'a?b/c:d@e' == url.raw_fragment


def test_fragment_non_ascii():
    url = URL('http://example.com/path#якорь')
    assert 'якорь' == url.fragment


def test_raw_parts_empty():
    url = URL('http://example.com')
    assert ('/',) == url.raw_parts


def test_raw_parts():
    url = URL('http://example.com/path/to')
    assert ('/', 'path', 'to') == url.raw_parts


def test_raw_parts_without_path():
    url = URL('http://example.com')
    assert ('/',) == url.raw_parts


def test_raw_path_parts_with_2F_in_path():
    url = URL('http://example.com/path%2Fto/three')
    assert ('/', 'path%2Fto', 'three') == url.raw_parts


def test_raw_path_parts_with_2f_in_path():
    url = URL('http://example.com/path%2fto/three')
    assert ('/', 'path%2Fto', 'three') == url.raw_parts


def test_raw_parts_for_relative_path():
    url = URL('path/to')
    assert ('path', 'to') == url.raw_parts


def test_raw_parts_for_relative_path_starting_from_slash():
    url = URL('/path/to')
    assert ('/', 'path', 'to') == url.raw_parts


def test_raw_parts_for_relative_double_path():
    url = URL('path/to')
    assert url.raw_parts == url.raw_parts


def test_parts_for_empty_url():
    url = URL()
    assert ('',) == url.raw_parts


def test_raw_parts_non_ascii():
    url = URL('http://example.com/путь/сюда')
    assert ('/',
            '%D0%BF%D1%83%D1%82%D1%8C',
            '%D1%81%D1%8E%D0%B4%D0%B0') == url.raw_parts


def test_parts_non_ascii():
    url = URL('http://example.com/путь/сюда')
    assert ('/',
            'путь',
            'сюда') == url.parts


def test_name_for_empty_url():
    url = URL()
    assert '' == url.raw_name


def test_raw_name():
    url = URL('http://example.com/path/to#frag')
    assert 'to' == url.raw_name


def test_raw_name_root():
    url = URL('http://example.com/#frag')
    assert '' == url.raw_name


def test_raw_name_root2():
    url = URL('http://example.com')
    assert '' == url.raw_name


def test_raw_name_root3():
    url = URL('http://example.com/')
    assert '' == url.raw_name


def test_relative_raw_name():
    url = URL('path/to')
    assert 'to' == url.raw_name


def test_relative_raw_name_starting_from_slash():
    url = URL('/path/to')
    assert 'to' == url.raw_name


def test_relative_raw_name_slash():
    url = URL('/')
    assert '' == url.raw_name


def test_name_non_ascii():
    url = URL('http://example.com/путь')
    assert url.name == 'путь'


def test_plus_in_path():
    url = URL('http://example.com/test/x+y%2Bz/:+%2B/')
    assert '/test/x+y+z/:++/' == url.path


# modifiers


def test_parent_raw_path():
    url = URL('http://example.com/path/to')
    assert url.parent.raw_path == '/path'


def test_parent_raw_parts():
    url = URL('http://example.com/path/to')
    assert url.parent.raw_parts == ('/', 'path')


def test_double_parent_raw_path():
    url = URL('http://example.com/path/to')
    assert url.parent.parent.raw_path == '/'


def test_empty_parent_raw_path():
    url = URL('http://example.com/')
    assert url.parent.parent.raw_path == '/'


def test_empty_parent_raw_path2():
    url = URL('http://example.com')
    assert url.parent.parent.raw_path == '/'


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


# truediv

def test_div_root():
    url = URL('http://example.com')
    assert str(url / 'path' / 'to') == 'http://example.com/path/to'


def test_div_root_with_slash():
    url = URL('http://example.com/')
    assert str(url / 'path' / 'to') == 'http://example.com/path/to'


def test_div():
    url = URL('http://example.com/path')
    assert str(url / 'to') == 'http://example.com/path/to'


def test_div_with_slash():
    url = URL('http://example.com/path/')
    assert str(url / 'to') == 'http://example.com/path/to'


def test_div_path_starting_from_slash_is_forbidden():
    url = URL('http://example.com/path/')
    with pytest.raises(ValueError):
        url / '/to/others'


def test_div_cleanup_query_and_fragment():
    url = URL('http://example.com/path?a=1#frag')
    assert str(url / 'to') == 'http://example.com/path/to'


def test_div_for_empty_url():
    url = URL() / 'a'
    assert url.raw_parts == ('a',)


def test_div_for_relative_url():
    url = URL('a') / 'b'
    assert url.raw_parts == ('a', 'b')


def test_div_for_relative_url_started_with_slash():
    url = URL('/a') / 'b'
    assert url.raw_parts == ('/', 'a', 'b')


def test_div_non_ascii():
    url = URL('http://example.com/path')
    url2 = url / 'сюда'
    assert url2.path == '/path/сюда'
    assert url2.raw_path == '/path/%D1%81%D1%8E%D0%B4%D0%B0'
    assert url2.parts == ('/', 'path', 'сюда')
    assert url2.raw_parts == ('/', 'path', '%D1%81%D1%8E%D0%B4%D0%B0')


def test_div_with_colon_and_at():
    url = URL('http://example.com/base') / 'path:abc@123'
    assert url.raw_path == '/base/path:abc@123'


def test_div_with_dots():
    url = URL('http://example.com/base') / '../path/./to'
    assert url.raw_path == '/path/to'


# with_path


def test_with_path():
    url = URL('http://example.com')
    assert str(url.with_path('/test')) == 'http://example.com/test'


def test_with_path_encoded():
    url = URL('http://example.com')
    assert str(url.with_path('/test',
                             encoded=True)
               ) == 'http://example.com/test'


def test_with_path_dots():
    url = URL('http://example.com')
    assert str(url.with_path('/test/.')) == 'http://example.com/test/'


def test_with_path_relative():
    url = URL('/path')
    assert str(url.with_path('/new')) == '/new'


def test_with_path_query():
    url = URL('http://example.com?a=b')
    assert str(url.with_path('/test')) == 'http://example.com/test'


def test_with_path_fragment():
    url = URL('http://example.com#frag')
    assert str(url.with_path('/test')) == 'http://example.com/test'


def test_with_path_empty():
    url = URL('http://example.com/test')
    assert str(url.with_path('')) == 'http://example.com'


def test_with_path_leading_slash():
    url = URL('http://example.com')
    assert url.with_path('test').path == '/test'


# with_fragment

def test_with_fragment():
    url = URL('http://example.com')
    assert str(url.with_fragment('frag')) == 'http://example.com/#frag'


def test_with_fragment_safe():
    url = URL('http://example.com')
    u2 = url.with_fragment('a:b?c@d/e')
    assert str(u2) == 'http://example.com/#a:b?c@d/e'


def test_with_fragment_non_ascii():
    url = URL('http://example.com')
    url2 = url.with_fragment('фрагм')
    assert url2.raw_fragment == '%D1%84%D1%80%D0%B0%D0%B3%D0%BC'
    assert url2.fragment == 'фрагм'


def test_with_fragment_None():
    url = URL('http://example.com/path#frag')
    url2 = url.with_fragment(None)
    assert str(url2) == 'http://example.com/path'


def test_with_fragment_bad_type():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        url.with_fragment(123)

# with_name


def test_with_name():
    url = URL('http://example.com/a/b')
    assert url.raw_parts == ('/', 'a', 'b')
    url2 = url.with_name('c')
    assert url2.raw_parts == ('/', 'a', 'c')


def test_with_name_for_naked_path():
    url = URL('http://example.com')
    url2 = url.with_name('a')
    assert url2.raw_parts == ('/', 'a')


def test_with_name_for_relative_path():
    url = URL('a')
    url2 = url.with_name('b')
    assert url2.raw_parts == ('b',)


def test_with_name_for_relative_path2():
    url = URL('a/b')
    url2 = url.with_name('c')
    assert url2.raw_parts == ('a', 'c')


def test_with_name_for_relative_path_starting_from_slash():
    url = URL('/a')
    url2 = url.with_name('b')
    assert url2.raw_parts == ('/', 'b')


def test_with_name_for_relative_path_starting_from_slash2():
    url = URL('/a/b')
    url2 = url.with_name('c')
    assert url2.raw_parts == ('/', 'a', 'c')


def test_with_name_empty():
    url = URL('http://example.com/path/to').with_name('')
    assert str(url) == 'http://example.com/path/'


def test_with_name_non_ascii():
    url = URL('http://example.com/path').with_name('путь')
    assert url.path == '/путь'
    assert url.raw_path == '/%D0%BF%D1%83%D1%82%D1%8C'
    assert url.parts == ('/', 'путь')
    assert url.raw_parts == ('/', '%D0%BF%D1%83%D1%82%D1%8C')


def test_with_name_with_slash():
    with pytest.raises(ValueError):
        URL('http://example.com').with_name('a/b')


def test_with_name_non_str():
    with pytest.raises(TypeError):
        URL('http://example.com').with_name(123)


def test_with_name_within_colon_and_at():
    url = URL('http://example.com/oldpath').with_name('path:abc@123')
    assert url.raw_path == '/path:abc@123'


def test_with_name_dot():
    with pytest.raises(ValueError):
        URL('http://example.com').with_name('.')


def test_with_name_double_dot():
    with pytest.raises(ValueError):
        URL('http://example.com').with_name('..')

# is_absolute


def test_is_absolute_for_relative_url():
    url = URL('/path/to')
    assert not url.is_absolute()


def test_is_absolute_for_absolute_url():
    url = URL('http://example.com')
    assert url.is_absolute()


def test_is_non_absolute_for_empty_url():
    url = URL()
    assert not url.is_absolute()


def test_is_non_absolute_for_empty_url2():
    url = URL('')
    assert not url.is_absolute()


def test_is_absolute_path_starting_from_double_slash():
    url = URL('//www.python.org')
    assert url.is_absolute()


# is_default_port

def test_is_default_port_for_relative_url():
    url = URL('/path/to')
    assert not url.is_default_port()


def test_is_default_port_for_absolute_url_without_port():
    url = URL('http://example.com')
    assert url.is_default_port()


def test_is_default_port_for_absolute_url_with_default_port():
    url = URL('http://example.com:80')
    assert url.is_default_port()


def test_is_default_port_for_absolute_url_with_nondefault_port():
    url = URL('http://example.com:8080')
    assert not url.is_default_port()


def test_is_default_port_for_unknown_scheme():
    url = URL('unknown://example.com:8080')
    assert not url.is_default_port()


#


def test_no_scheme():
    url = URL('example.com')
    assert url.raw_host is None
    assert url.raw_path == 'example.com'
    assert str(url) == 'example.com'


def test_no_scheme2():
    url = URL('example.com/a/b')
    assert url.raw_host is None
    assert url.raw_path == 'example.com/a/b'
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


def test_fragment_only_url():
    url = URL('#frag')
    assert str(url) == "#frag"


def test_url_from_url():
    url = URL('http://example.com')
    assert URL(url) == url
    assert URL(url).raw_parts == ('/',)


def test_lowercase_scheme():
    url = URL('HTTP://example.com')
    assert str(url) == 'http://example.com'


def test_str_for_empty_url():
    url = URL()
    assert '' == str(url)


def test_parent_for_empty_url():
    url = URL()
    assert url is url.parent


def test_empty_value_for_query():
    url = URL('http://example.com/path').with_query({'a': ''})
    assert str(url) == 'http://example.com/path?a='


@pytest.mark.xfail
def test_none_value_for_query():
    url = URL('http://example.com/path').with_query({'a': None})
    assert str(url) == 'http://example.com/path?a'


def test_decode_pct_in_path():
    url = URL('http://www.python.org/%7Eguido')
    assert 'http://www.python.org/~guido' == str(url)


def test_decode_pct_in_path_lower_case():
    url = URL('http://www.python.org/%7eguido')
    assert 'http://www.python.org/~guido' == str(url)

# join


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


def test_split_result_non_decoded():
    with pytest.raises(ValueError):
        URL(SplitResult('http', 'example.com', 'path', 'qs', 'frag'))


def test_human_repr():
    url = URL('http://вася:пароль@хост.домен:8080/путь/сюда?арг=вал#фраг')
    s = url.human_repr()
    assert s == 'http://вася:пароль@хост.домен:8080/путь/сюда?арг=вал#фраг'


def test_human_repr_defaults():
    url = URL('путь')
    s = url.human_repr()
    assert s == 'путь'


def test_human_repr_default_port():
    url = URL('http://вася:пароль@хост.домен/путь/сюда?арг=вал#фраг')
    s = url.human_repr()
    assert s == 'http://вася:пароль@хост.домен/путь/сюда?арг=вал#фраг'


# relative

def test_relative():
    url = URL('http://user:pass@example.com:8080/path?a=b#frag')
    rel = url.relative()
    assert str(rel) == '/path?a=b#frag'


def test_relative_is_relative():
    url = URL('http://user:pass@example.com:8080/path?a=b#frag')
    rel = url.relative()
    assert not rel.is_absolute()


def test_relative_abs_parts_are_removed():
    url = URL('http://user:pass@example.com:8080/path?a=b#frag')
    rel = url.relative()
    assert not rel.scheme
    assert not rel.user
    assert not rel.password
    assert not rel.host
    assert not rel.port


def test_relative_fails_on_rel_url():
    with pytest.raises(ValueError):
        URL('/path?a=b#frag').relative()


def test_slash_and_question_in_query():
    u = URL('http://example.com/path?http://example.com/p?a#b')
    assert u.query_string == 'http://example.com/p?a'


def test_slash_and_question_in_fragment():
    u = URL('http://example.com/path#http://example.com/p?a')
    assert u.fragment == 'http://example.com/p?a'


def test_requoting():
    u = URL('http://127.0.0.1/?next=http%3A//example.com/')
    assert u.raw_query_string == 'next=http://example.com/'
    assert str(u) == 'http://127.0.0.1/?next=http://example.com/'
