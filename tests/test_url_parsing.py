from yarl import URL


class TestScheme:

    def test_scheme_path(self):
        u = URL('scheme:path')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == 'path'

    def test_scheme_path_other(self):
        u = URL('scheme:path:other')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == 'path:other'

    def test_complex_scheme(self):
        u = URL('allow+chars-33.:path')
        assert u.scheme == 'allow+chars-33.'
        assert u.host is None
        assert u.path == 'path'

    def test_scheme_only(self):
        u = URL('simple:')
        assert u.scheme == 'simple'
        assert u.host is None
        assert u.path == ''

    def test_no_scheme1(self):
        u = URL('google.com:80')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == 'google.com:80'

    def test_no_scheme2(self):
        u = URL('google.com:80/root')
        assert u.scheme == 'google.com'
        assert u.host is None
        assert u.path == '80/root'

    def test_not_a_scheme1(self):
        u = URL('not_cheme:path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == 'not_cheme:path'

    def test_not_a_scheme2(self):
        u = URL('37signals:book')
        assert u.scheme == '37signals'
        assert u.host is None
        assert u.path == 'book'

    def test_scheme_rel_path1(self):
        u = URL(':relative-path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == ':relative-path'

    def test_scheme_rel_path2(self):
        u = URL(':relative/path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == ':relative/path'

    def test_scheme_weird(self):
        u = URL('://and-this')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == '://and-this'


class TestHost:

    def test_canonical(self):
        u = URL('scheme://host/path')
        assert u.scheme == 'scheme'
        assert u.host == 'host'
        assert u.path == '/path'

    def test_absolute_no_scheme(self):
        u = URL('//host/path')
        assert u.scheme == ''
        assert u.host == 'host'
        assert u.path == '/path'

    def test_absolute_no_scheme_complex_host(self):
        u = URL('//host+path')
        assert u.scheme == ''
        assert u.host == 'host+path'
        assert u.path == '/'

    def test_absolute_no_scheme_simple_host(self):
        u = URL('//host')
        assert u.scheme == ''
        assert u.host == 'host'
        assert u.path == '/'

    def test_weird_host(self):
        u = URL('//this+is$also&host!')
        assert u.scheme == ''
        assert u.host == 'this+is$also&host!'
        assert u.path == '/'

    def test_scheme_no_host(self):
        u = URL('scheme:/host/path')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == '/host/path'

    def test_scheme_no_host2(self):
        u = URL('scheme:///host/path')
        assert u.scheme == 'scheme'
        assert u.host is None
        assert u.path == '/host/path'

    def test_no_scheme_no_host(self):
        u = URL('scheme//host/path')
        assert u.scheme == ''
        assert u.host is None
        assert u.path == 'scheme//host/path'

    def test_ipv4(self):
        u = URL('//127.0.0.1/')
        assert u.scheme == ''
        assert u.host == '127.0.0.1'
        assert u.path == '/'

    def test_masked_ipv4(self):
        u = URL('//[127.0.0.1]/')
        assert u.scheme == ''
        assert u.host == '127.0.0.1'
        assert u.path == '/'

    def test_ipv6(self):
        u = URL('//[::1]/')
        assert u.scheme == ''
        assert u.host == '::1'
        assert u.path == '/'

    def test_strange_ip(self):
        u = URL('//[-1]/')
        assert u.scheme == ''
        assert u.host == '-1'
        assert u.path == '/'

    def test_strange_ip_2(self):
        u = URL('//[v1.-1]/')
        assert u.scheme == ''
        assert u.host == 'v1.-1'
        assert u.path == '/'

    def test_strange_ip_3(self):
        u = URL('//v1.[::1]/')
        assert u.scheme == ''
        assert u.host == '::1'
        assert u.path == '/'
