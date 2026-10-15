"""WHATWG mode reads "\\" as "/" in special URLs; RFC 3986 mode rejects it."""

import pickle
from collections.abc import Callable

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://a:b@c\\", "http://a:b@c/"),
        ("ws://a@b\\c", "ws://a@b/c"),
        ("http:\\\\foo.com\\bar", "http://foo.com/bar"),
        ("HTTPS://h\\a\\b", "https://h/a/b"),
        ("file:\\\\server\\share", "file://server/share"),
        # The query and the fragment keep it.
        ("http://h/a\\b?c\\d#e\\f", "http://h/a/b?c%5Cd#e%5Cf"),
        ("http://h/a\\b#e\\f?g\\h", "http://h/a/b#e%5Cf?g%5Ch"),
        ("http://h/a\\b?c#e\\f", "http://h/a/b?c#e%5Cf"),
        # Leading C0 control or space, tab and newline are dropped first.
        (" \thttp://h\\a", "http://h/a"),
        ("ht\ntp://h\\a", "http://h/a"),
    ],
)
def test_special(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc://h/a\\b", "sc://h/a%5Cb"),
        ("c:\\foo", "c:%5Cfoo"),
    ],
)
def test_non_special(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        # The base is not known yet, so "\\" stays a character.
        ("\\x", "%5Cx"),
        ("\\/a", "%5C/a"),
        ("\\\\x\\hello", "%5C%5Cx%5Chello"),
        ("a\\b:c", "a%5Cb:c"),
        # A network-path reference has an authority either way.
        ("//h\\p", "//h/p"),
        (" //h\\p", "//h/p"),
    ],
)
def test_relative(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("\\x", "http://example.org/x"),
        ("\\\\x\\hello", "http://x/hello"),
        (":foo.com\\", "http://example.org/foo/:foo.com/"),
        ("x\\y?a\\b", "http://example.org/foo/x/y?a%5Cb"),
        ("http:\\\\a\\b:c\\d@foo.com\\", "http://a/b:c/d@foo.com/"),
    ],
)
def test_join(reference: str, expected: str) -> None:
    url = URL("http://example.org/foo/bar").join(URL(reference))
    assert str(url) == expected


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        # A non-special base keeps its host: "\\/a" is not "//a" there.
        ("\\/a", "foo://foo/%5C/a"),
        ("\\\\a", "foo://foo/%5C%5Ca"),
        ("\\a", "foo://foo/%5Ca"),
    ],
)
def test_join_non_special_base(reference: str, expected: str) -> None:
    url = URL("foo://foo/a").join(URL(reference))
    assert str(url) == expected
    assert url.host == "foo"


@pytest.mark.parametrize(
    ("modify", "expected"),
    [
        (lambda u: u.with_query("a=1"), "http://x/hello?a=1#f"),
        (lambda u: u.with_query(None), "http://x/hello#f"),
        (lambda u: u.extend_query(a=1), "http://x/hello?q=0&a=1#f"),
        (lambda u: u.update_query(a=1), "http://x/hello?q=0&a=1#f"),
        (lambda u: u % {"a": 1}, "http://x/hello?q=0&a=1#f"),
        (lambda u: u.without_query_params("q"), "http://x/hello#f"),
        (lambda u: u.with_fragment("g"), "http://x/hello?q=0#g"),
        (lambda u: u.with_fragment(None), "http://x/hello?q=0"),
        # Another path makes it an ordinary relative reference.
        (lambda u: u.with_path("p"), "http://example.org/p"),
    ],
)
def test_join_after_modification(modify: Callable[[URL], URL], expected: str) -> None:
    url = modify(URL("\\\\x\\hello?q=0#f"))
    assert str(URL("http://example.org/foo/bar").join(url)) == expected


def test_join_after_modification_empty_query() -> None:
    url = URL("\\\\x\\hello?#").with_fragment("f")
    assert str(URL("http://example.org/").join(url)) == "http://x/hello?#f"


def test_join_rfc_base() -> None:
    # An RFC 3986 mode base does not read "\\" as "/" either.
    url = URL("http://example.org/foo/bar", mode="rfc").join(URL("\\\\x"))
    assert str(url) == "http://example.org/foo/%5C%5Cx"


def test_pickle() -> None:
    url = pickle.loads(pickle.dumps(URL("\\\\x\\hello")))
    assert str(URL("http://example.org/").join(url)) == "http://x/hello"
    assert str(URL("foo://foo/").join(url)) == "foo://foo/%5C%5Cx%5Chello"


@pytest.mark.parametrize(
    "url", ["http://h/a\\b", "sc://h/a\\b", "\\x", "http://h/?a\\b", "c:\\foo"]
)
def test_rfc_mode(url: str) -> None:
    with pytest.raises(ValueError, match="RFC 3986 does not allow"):
        URL(url, mode="rfc")


def test_encoded() -> None:
    # A pre-encoded URL is taken as is.
    assert URL("http://h/a\\b", encoded=True).raw_path == "/a\\b"


def test_human_repr_round_trip() -> None:
    url = URL.build(scheme="http", host="h", path="/a\\b", query_string="c\\d=e")
    assert url.path == "/a\\b"
    assert url.human_repr() == "http://h/a%5Cb?c\\d=e"
    assert URL(url.human_repr()) == url


def test_build_keeps_backslash() -> None:
    # Built parts are not parsed, so "\\" is a character of the path.
    url = URL.build(scheme="http", host="h", path="/a\\b", mode="rfc")
    assert str(url) == "http://h/a%5Cb"
