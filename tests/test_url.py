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
