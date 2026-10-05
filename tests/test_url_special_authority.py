"""Special-scheme URLs without "//" or with extra slashes before the host.

The WHATWG URL Standard skips the slashes after the scheme of a special URL
other than file, so "http:example.com/", "http:/example.com/" and
"http:///example.com/" are all "http://example.com/". Against a base with the
same scheme an input without "//" is a relative reference instead. yarl
follows that in WHATWG mode; RFC 3986 mode keeps such a URL without a host.
"""

import pickle
from collections.abc import Callable

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http:example.com/", "http://example.com/"),
        ("http:/example.com/", "http://example.com/"),
        ("https:example.com/a/b", "https://example.com/a/b"),
        ("ws:/example.com:8080", "ws://example.com:8080"),
        ("wss:example.com", "wss://example.com"),
        ("ftp:/example.com/", "ftp://example.com/"),
        ("HTTP:Example.COM/p", "http://example.com/p"),
        ("http:a:b@example.com/", "http://a:b@example.com/"),
        ("http:@example.com/", "http://example.com/"),
        ("http:example.com?q#f", "http://example.com/?q#f"),
        ("http:example.com/p?#", "http://example.com/p?#"),
        ("http:example.com/%7e", "http://example.com/~"),
        ("http:///example.com/", "http://example.com/"),
        ("https:////example.com/a?q#f", "https://example.com/a?q#f"),
        ("ws:///a:b@example.com:8080", "ws://a:b@example.com:8080"),
    ],
)
def test_parsed_as_authority(url: str, expected: str) -> None:
    assert str(URL(url)) == expected
    assert URL(url) == URL(expected)


@pytest.mark.parametrize("url", ["http:/example.com/%7e", "http:///example.com/%7e"])
def test_parsed_as_authority_encoded(url: str) -> None:
    parsed = URL(url, encoded=True)
    assert str(parsed) == "http://example.com/%7e"
    assert parsed.host == "example.com"


@pytest.mark.parametrize(
    "url",
    [
        "http:@/www.example.com",
        "http:/:@/www.example.com",
        "http:a:b@/www.example.com",
        "http:@:www.example.com",
        "https:[61:27]/:foo",
        "http:foo.123/",
        "http:///@/www.example.com",
    ],
)
def test_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        URL(url)


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        # Nothing to read as a host: kept as a reference to a base.
        ("http:", "http:", "http:"),
        ("http:/", "http:/", "http:/"),
        ("http:?q", "http:?q", "http:?q"),
        # file and non-special schemes are not affected.
        ("file:p", "file:///p", "file:p"),
        ("sc:example.com/", "sc:example.com/", "sc:example.com/"),
    ],
)
def test_kept_without_authority(url: str, whatwg: str, rfc: str) -> None:
    assert URL(url).raw_host is None
    assert str(URL(url)) == whatwg
    assert str(URL(url, mode="rfc")) == rfc


@pytest.mark.parametrize(
    "url",
    [
        "http:example.com/",
        "http:/example.com/",
        "http:@/www.example.com",
        "http:///example.com/",
    ],
)
def test_rfc_mode_keeps_path(url: str) -> None:
    parsed = URL(url, mode="rfc")
    assert parsed.raw_host is None
    assert str(parsed) == url


@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        ("http://h/foo/bar", "http:example.com/", "http://h/foo/example.com/"),
        ("http://h/foo/bar", "http:/example.com/", "http://h/example.com/"),
        ("http://h/foo/bar", "http::@c:29", "http://h/foo/:@c:29"),
        ("http://h/foo/bar", "http:g?q#f", "http://h/foo/g?q#f"),
        ("http://h/foo/bar", "http:g?#", "http://h/foo/g?#"),
        ("http://h/foo/bar", "http:../g", "http://h/g"),
        ("http://h/foo/bar", "https:example.com/", "https://example.com/"),
        ("http://h/foo/bar", "ftp:/example.com/", "ftp://example.com/"),
        ("sc://h/foo/bar", "http:example.com/", "http://example.com/"),
        # With "//" the input is absolute against any base, as in WHATWG.
        ("http://h/foo/bar", "http:///example.com/", "http://example.com/"),
        ("http://h/foo/bar", "http:////example.com/p", "http://example.com/p"),
    ],
)
def test_join(base: str, reference: str, expected: str) -> None:
    assert str(URL(base).join(URL(reference))) == expected
    encoded = URL(base, encoded=True).join(URL(reference, encoded=True))
    assert str(encoded) == expected


def test_join_rfc_base() -> None:
    # An RFC mode base is a strict parser (RFC 3986 section 5.2.2): the
    # reference, "http://example.com/" in WHATWG mode, is used as is.
    base = URL("http://h/foo/bar", mode="rfc")
    joined = base.join(URL("http:example.com/"))
    assert str(joined) == "http://example.com/"
    assert joined.mode == "rfc"


@pytest.mark.parametrize(
    ("modify", "expected"),
    [
        (lambda u: u.with_query("a=1"), "http://h/foo/example.com/?a=1#g"),
        (lambda u: u.with_query(None), "http://h/foo/example.com/#g"),
        (lambda u: u.extend_query(a=1), "http://h/foo/example.com/?b=2&a=1#g"),
        (lambda u: u.update_query(a=1), "http://h/foo/example.com/?b=2&a=1#g"),
        (lambda u: u % {"a": 1}, "http://h/foo/example.com/?b=2&a=1#g"),
        (lambda u: u.without_query_params("b"), "http://h/foo/example.com/#g"),
        (lambda u: u.with_fragment("f"), "http://h/foo/example.com/?b=2#f"),
        (lambda u: u.with_fragment(None), "http://h/foo/example.com/?b=2"),
    ],
)
def test_join_after_query_or_fragment_change(
    modify: Callable[[URL], URL], expected: str
) -> None:
    # "http:example.com/?a=1" is still a relative reference for WHATWG.
    url = modify(URL("http:example.com/?b=2#g"))
    assert str(URL("http://h/foo/bar").join(url)) == expected


def test_join_after_fragment_change_does_not_share() -> None:
    # with_fragment() must not hand the join path to a URL shared through
    # the from_parts() cache.
    URL("http:example.com/").with_fragment("f")
    url = URL("http://example.com/").with_fragment("f")
    assert str(URL("http://h/foo/bar").join(url)) == "http://example.com/#f"


def test_join_after_modification() -> None:
    # A URL with another path or host is an ordinary absolute URL.
    url = URL("http:example.com/").with_path("/p")
    assert str(URL("http://h/foo/bar").join(url)) == "http://example.com/p"
    url = URL("http:example.com/").with_host("other.com")
    assert str(URL("http://h/foo/bar").join(url)) == "http://other.com/"


def test_join_after_mode_change() -> None:
    url = URL(URL("http:example.com/"), mode="rfc")
    assert str(url) == "http://example.com/"
    assert str(URL("http://h/foo/bar").join(url)) == "http://example.com/"


def test_pickle_keeps_join_path() -> None:
    url = pickle.loads(pickle.dumps(URL("http:example.com/")))
    assert str(url) == "http://example.com/"
    assert str(URL("http://h/foo/bar").join(url)) == "http://h/foo/example.com/"


@pytest.mark.parametrize("url", ["http://example.com/", "http:///example.com/"])
def test_pickle_without_join_path(url: str) -> None:
    parsed = URL(url)
    assert len(parsed.__getstate__()) == 3
    loaded = pickle.loads(pickle.dumps(parsed))
    assert str(URL("http://h/foo/bar").join(loaded)) == "http://example.com/"
