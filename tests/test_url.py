import sys
import pickle
import pytest
from urllib.parse import SplitResult, urlencode
from multidict import MultiDict, MultiDictProxy

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


# comparison and hashing

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


# with_*


def test_with_scheme():
    url = URL('http://example.com')
    assert str(url.with_scheme('https')) == 'https://example.com'


def test_with_scheme_uppercased():
    url = URL('http://example.com')
    assert str(url.with_scheme('HTTPS')) == 'https://example.com'


def test_with_scheme_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_scheme('http')


def test_with_scheme_invalid_type():
    url = URL('http://example.com')
    with pytest.raises(TypeError):
        assert str(url.with_scheme(123))


def test_with_user():
    url = URL('http://example.com')
    assert str(url.with_user('john')) == 'http://john@example.com'


def test_with_user_non_ascii():
    url = URL('http://example.com')
    url2 = url.with_user('вася')
    assert url2.raw_user == '%D0%B2%D0%B0%D1%81%D1%8F'
    assert url2.user == 'вася'


def test_with_user_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_user('user')


def test_with_user_invalid_type():
    url = URL('http://example.com:123')
    with pytest.raises(TypeError):
        url.with_user(123)


def test_with_user_None():
    url = URL('http://john@example.com')
    assert str(url.with_user(None)) == 'http://example.com'


def test_with_user_None_when_password_present():
    url = URL('http://john:pass@example.com')
    assert str(url.with_user(None)) == 'http://example.com'


def test_with_password():
    url = URL('http://john@example.com')
    assert str(url.with_password('pass')) == 'http://john:pass@example.com'


def test_with_password_non_ascii():
    url = URL('http://john@example.com')
    url2 = url.with_password('пароль')
    assert url2.raw_password == '%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C'
    assert url2.password == 'пароль'


def test_with_password_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_password('pass')


def test_with_password_None():
    url = URL('http://john:pass@example.com')
    assert str(url.with_password(None)) == 'http://john@example.com'


def test_with_password_invalid_type():
    url = URL('http://example.com:123')
    with pytest.raises(TypeError):
        url.with_password(123)


def test_with_password_and_empty_user():
    url = URL('http://example.com')
    with pytest.raises(ValueError):
        assert str(url.with_password('pass'))


def test_from_str_with_host_ipv4():
    url = URL('http://host:80')
    url = url.with_host('192.168.1.1')
    assert url.raw_host == '192.168.1.1'


def test_from_str_with_host_ipv6():
    url = URL('http://host:80')
    url = url.with_host('::1')
    assert url.raw_host == '::1'


def test_with_host():
    url = URL('http://example.com:123')
    assert str(url.with_host('example.org')) == 'http://example.org:123'


def test_with_host_empty():
    url = URL('http://example.com:123')
    with pytest.raises(ValueError):
        url.with_host('')


def test_with_host_non_ascii():
    url = URL('http://example.com:123')
    url2 = url.with_host('историк.рф')
    assert url2.raw_host == 'xn--h1aagokeh.xn--p1ai'
    assert url2.host == 'историк.рф'


def test_with_host_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_host('example.com')


def test_with_host_invalid_type():
    url = URL('http://example.com:123')
    with pytest.raises(TypeError):
        url.with_host(None)


def test_with_port():
    url = URL('http://example.com')
    assert str(url.with_port(8888)) == 'http://example.com:8888'


def test_with_port_keeps_query_and_fragment():
    url = URL('http://example.com/?a=1#frag')
    assert str(url.with_port(8888)) == 'http://example.com:8888/?a=1#frag'


def test_with_port_for_relative_url():
    with pytest.raises(ValueError):
        URL('path/to').with_port(1234)


def test_with_port_invalid_type():
    with pytest.raises(TypeError):
        URL('http://example.com').with_port('123')


def test_with_path():
    url = URL('http://example.com')
    assert str(url.with_path('/test')) == 'http://example.com/test'


def test_with_path_encoded():
    url = URL('http://example.com')
    assert str(url.with_path('/test',
                             encoded=True)
               ) == 'http://example.com/test'


def test_with_query():
    url = URL('http://example.com')
    assert str(url.with_query({'a': '1'})) == 'http://example.com/?a=1'


def test_update_query():
    url = URL('http://example.com/')
    assert str(url.update_query({'a': '1'})) == 'http://example.com/?a=1'

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
    url2 = url.with_query({'a+b': '?=+&'})
    assert url2.raw_query_string == 'a%2Bb=?%3D%2B%26'
    assert url2.query_string == 'a%2Bb=?%3D%2B%26'
    assert url2.query == {'a+b': '?=+&'}


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


# serialize

def test_pickle():
    u1 = URL('test')
    hash(u1)
    v = pickle.dumps(u1)
    u2 = pickle.loads(v)
    assert u1._cache
    assert not u2._cache
    assert hash(u1) == hash(u2)


def test_default_style_state():
    u = URL('test')
    hash(u)
    u.__setstate__((None, {
        '_val': 'test',
        '_strict': False,
        '_cache': {'hash': 1},
    }))
    assert not u._cache
    assert u._val == 'test'
    assert u._strict is False


# build classmethod

def test_build_without_arguments():
    u = URL.build()
    assert str(u) == ''


def test_build_simple():
    u = URL.build(scheme='http', host='127.0.0.1')
    assert str(u) == 'http://127.0.0.1'


def test_build_scheme_and_host():
    with pytest.raises(ValueError):
        URL.build(host='127.0.0.1')

    with pytest.raises(ValueError):
        URL.build(scheme='http')


def test_build_with_port():
    u = URL.build(scheme='http', host='127.0.0.1', port=8000)
    assert str(u) == 'http://127.0.0.1:8000'


def test_build_with_user():
    u = URL.build(scheme='http', host='127.0.0.1', user='foo')
    assert str(u) == 'http://foo@127.0.0.1'


def test_build_with_user_password():
    u = URL.build(scheme='http', host='127.0.0.1', user='foo', password='bar')
    assert str(u) == 'http://foo:bar@127.0.0.1'


def test_build_with_query_and_query_string():
    with pytest.raises(ValueError):
        URL.build(
            scheme='http',
            host='127.0.0.1',
            user='foo',
            password='bar',
            port=8000,
            path='/index.html',
            query=dict(arg="value1"),
            query_string="arg=value1",
            fragment="top"
        )


def test_build_with_all():
    u = URL.build(
        scheme='http',
        host='127.0.0.1',
        user='foo',
        password='bar',
        port=8000,
        path='/index.html',
        query_string="arg=value1",
        fragment="top"
    )
    assert str(u) == 'http://foo:bar@127.0.0.1:8000/index.html?arg=value1#top'


def test_query_str():
    u = URL.build(
        scheme='http',
        host='127.0.0.1',
        path='/',
        query_string="arg=value1"
    )
    assert str(u) == 'http://127.0.0.1/?arg=value1'


def test_query_dict():
    u = URL.build(
        scheme='http',
        host='127.0.0.1',
        path='/',
        query=dict(arg="value1")
    )

    assert str(u) == 'http://127.0.0.1/?arg=value1'


def test_build_path_quoting():
    u = URL.build(
        scheme='http',
        host='127.0.0.1',
        path='/файл.jpg',
        query=dict(arg="Привет")
    )

    assert u == URL('http://127.0.0.1/файл.jpg?arg=Привет')
    assert str(u) == ('http://127.0.0.1/%D1%84%D0%B0%D0%B9%D0%BB.jpg?'
                      'arg=%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82')


def test_build_query_quoting():
    u = URL.build(
        scheme='http',
        host='127.0.0.1',
        path='/файл.jpg',
        query="arg=Привет"
    )

    assert u == URL('http://127.0.0.1/файл.jpg?arg=Привет')
    assert str(u) == ('http://127.0.0.1/%D1%84%D0%B0%D0%B9%D0%BB.jpg?'
                      'arg=%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82')
