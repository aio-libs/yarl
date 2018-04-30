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
