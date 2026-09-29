"""WHATWG mode reads "\\" as "/" in special URLs; RFC 3986 mode rejects it."""

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
        ("\\x", "/x"),
        ("\\\\x\\hello", "//x/hello"),
        ("a\\b:c", "a/b:c"),
        (":\\", ":/"),
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
        ("http:\\\\a\\b:c\\d@foo.com\\", "http://a/b:c/d@foo.com/"),
    ],
)
def test_join(reference: str, expected: str) -> None:
    url = URL("http://example.org/foo/bar").join(URL(reference))
    assert str(url) == expected


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
