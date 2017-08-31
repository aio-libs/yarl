import pytest

from yarl import URL


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


def test_build_query_only():
    u = URL.build(
        query={'key': 'value'},
    )

    assert str(u) == '?key=value'


def test_build_drop_dots():
    u = URL.build(
        scheme='http',
        host='example.com',
        path='/path/../to',
    )
    assert str(u) == 'http://example.com/to'
