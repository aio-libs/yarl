import sys

import pytest

from yarl import URL


class TestScheme:

    def test_scheme_path(self):
        u = URL('scheme:path')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == 'path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_scheme_path_other(self):
        u = URL('scheme:path:other')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == 'path:other'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_complex_scheme(self):
        u = URL('allow+chars-33.:path')
        assert u.scheme == 'allow+chars-33.'
        assert u.host is None
        assert u.path == 'path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_scheme_only(self):
        u = URL('simple:')
        assert u.scheme == 'simple'
        assert u.host is None
        assert u.path == ''
        assert u.query_string == ''
        assert u.fragment == ''

    def test_no_scheme1(self):
        u = URL('google.com:80')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == 'google.com:80'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_no_scheme2(self):
        u = URL('google.com:80/root')
        assert u.scheme == 'google.com'
        assert u.host is None
        assert u.path == '80/root'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_not_a_scheme1(self):
        u = URL('not_cheme:path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == 'not_cheme:path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_not_a_scheme2(self):
        u = URL('37signals:book')
        assert u.scheme == '37signals'
        assert u.host is None
        assert u.path == 'book'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_scheme_rel_path1(self):
        u = URL(':relative-path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == ':relative-path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_scheme_rel_path2(self):
        u = URL(':relative/path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == ':relative/path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_scheme_weird(self):
        u = URL('://and-this')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == '://and-this'
        assert u.query_string == ''
        assert u.fragment == ''


class TestHost:

    def test_canonical(self):
        u = URL('scheme://host/path')
        assert u.scheme == 'scheme'
        assert u.host == 'host'
        assert u.path == '/path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_absolute_no_scheme(self):
        u = URL('//host/path')
        assert u.scheme == ''
        assert u.host == 'host'
        assert u.path == '/path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_absolute_no_scheme_complex_host(self):
        u = URL('//host+path')
        assert u.scheme == ''
        assert u.host == 'host+path'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_absolute_no_scheme_simple_host(self):
        u = URL('//host')
        assert u.scheme == ''
        assert u.host == 'host'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_weird_host(self):
        u = URL('//this+is$also&host!')
        assert u.scheme == ''
        assert u.host == 'this+is$also&host!'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_scheme_no_host(self):
        u = URL('scheme:/host/path')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == '/host/path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_scheme_no_host2(self):
        u = URL('scheme:///host/path')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == '/host/path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_no_scheme_no_host(self):
        u = URL('scheme//host/path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == 'scheme//host/path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_ipv4(self):
        u = URL('//127.0.0.1/')
        assert u.scheme == ''
        assert u.host == '127.0.0.1'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_masked_ipv4(self):
        u = URL('//[127.0.0.1]/')
        assert u.scheme == ''
        assert u.host == '127.0.0.1'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_ipv6(self):
        u = URL('//[::1]/')
        assert u.scheme == ''
        assert u.host == '::1'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_strange_ip(self):
        u = URL('//[-1]/')
        assert u.scheme == ''
        assert u.host == '-1'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_strange_ip_2(self):
        u = URL('//[v1.-1]/')
        assert u.scheme == ''
        assert u.host == 'v1.-1'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_strange_ip_3(self):
        u = URL('//v1.[::1]/')
        assert u.scheme == ''
        assert u.host == '::1'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''


class TestPort:

    def test_canonical(self):
        u = URL('//host:80/path')
        assert u.scheme == ''
        assert u.host == 'host'
        assert u.port == 80
        assert u.path == '/path'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_no_path(self):
        u = URL('//host:80')
        assert u.scheme == ''
        assert u.host == 'host'
        assert u.port == 80
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_no_host(self):
        with pytest.raises(ValueError):
            URL('//:80')

    def test_double_port(self):
        with pytest.raises(ValueError):
            URL('//h:22:80/')

    def test_bad_port(self):
        with pytest.raises(ValueError):
            URL('//h:no/path')

    def test_another_bad_port(self):
        with pytest.raises(ValueError):
            URL('//h:22:no/path')

    @pytest.mark.skipif(sys.version_info < (3, 6),
                        reason="Requires Python 3.6+")
    def test_bad_port_again(self):
        with pytest.raises(ValueError):
            URL('//h:-80/path')


class TestUserInfo:

    def test_canonical(self):
        u = URL('sch://user@host/')
        assert u.scheme == 'sch'
        assert u.user == 'user'
        assert u.host == 'host'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_user_pass(self):
        u = URL('//user:pass@host')
        assert u.scheme == ''
        assert u.user == 'user'
        assert u.password == 'pass'
        assert u.host == 'host'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_complex_userinfo(self):
        u = URL('//user:pas:and:more@host')
        assert u.scheme == ''
        assert u.user == 'user'
        assert u.password == 'pas:and:more'
        assert u.host == 'host'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_no_user(self):
        u = URL('//:pas:@host')
        assert u.scheme == ''
        assert u.user is None
        assert u.password == 'pas:'
        assert u.host == 'host'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_weird_user(self):
        u = URL("//!($&')*+,;=@host")
        assert u.scheme == ''
        assert u.user == "!($&')*+,;="
        assert u.password is None
        assert u.host == 'host'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_weird_user2(self):
        u = URL("//user@info@ya.ru")
        assert u.scheme == ''
        assert u.user == "user@info"
        assert u.password is None
        assert u.host == 'ya.ru'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''

    def test_weird_user3(self):
        u = URL("//[some]@host")
        assert u.scheme == ''
        assert u.user == "[some]"
        assert u.password is None
        assert u.host == 'host'
        assert u.path == '/'
        assert u.query_string == ''
        assert u.fragment == ''


class TestQuery_String:

    def test_simple(self):
        u = URL("?query")
        assert u.scheme == ''
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ''
        assert u.query_string == 'query'
        assert u.fragment == ''
