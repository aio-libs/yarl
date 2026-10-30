"""A "\\" outside the path of a special URL.

The WHATWG URL Standard reads "\\" as "/" only in the authority and the path
of a special URL. It is not in the path, opaque path, query or fragment
percent-encode sets, so it stays as written everywhere else. RFC 3986 does
not allow it, so RFC mode rejects it.
"""

import pickle

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "expected", "raw_path", "query_string", "fragment"),
    [
        ("non-special:\\\\opaque", "non-special:\\\\opaque", "\\\\opaque", "", ""),
        (
            "non-special:\\\\opaque/path",
            "non-special:\\\\opaque/path",
            "\\\\opaque/path",
            "",
            "",
        ),
        (
            "non-special:\\\\opaque\\path",
            "non-special:\\\\opaque\\path",
            "\\\\opaque\\path",
            "",
            "",
        ),
        ("non-special:\\/opaque", "non-special:\\/opaque", "\\/opaque", "", ""),
        ("non-special:/\\path", "non-special:/\\path", "/\\path", "", ""),
        (
            "non-special://host/a\\b",
            "non-special://host/a\\b",
            "/a\\b",
            "",
            "",
        ),
        ("sc:\\../", "sc:\\../", "\\../", "", ""),
        ("foo://h/a?b\\c#d\\e", "foo://h/a?b\\c#d\\e", "/a", "b\\c", "d\\e"),
        ("http://h/a?b\\c#d\\e", "http://h/a?b\\c#d\\e", "/a", "b\\c", "d\\e"),
        ("wss://h/a?b\\c#d\\e", "wss://h/a?b\\c#d\\e", "/a", "b\\c", "d\\e"),
        # An encoded "\\" stays encoded.
        ("foo://h/a%5cb\\c", "foo://h/a%5Cb\\c", "/a%5Cb\\c", "", ""),
    ],
)
def test_parse(
    url: str, expected: str, raw_path: str, query_string: str, fragment: str
) -> None:
    parsed = URL(url)
    assert str(parsed) == expected
    assert parsed.raw_path == raw_path
    assert parsed.path == raw_path.replace("%5C", "\\")
    assert parsed.raw_query_string == parsed.query_string == query_string
    assert parsed.raw_fragment == parsed.fragment == fragment
    assert URL(str(parsed)) == parsed
    assert pickle.loads(pickle.dumps(parsed)) == parsed


@pytest.mark.parametrize(
    ("reference", "base", "expected"),
    [
        ("\\a", "foo://foo/a", "foo://foo/\\a"),
        ("\\/a", "foo://foo/a", "foo://foo/\\/a"),
        ("\\\\a", "foo://foo/a", "foo://foo/\\\\a"),
        ("#\\", "http://example.org/foo/bar", "http://example.org/foo/bar#\\"),
        ("?a\\b", "http://h/x", "http://h/x?a\\b"),
        ("a\\b", "foo://h/x/", "foo://h/x/a\\b"),
        # A special base reads it as "/".
        ("\\a", "http://h/x", "http://h/a"),
        ("a\\b", "http://h/x/", "http://h/x/a/b"),
    ],
)
def test_join(reference: str, base: str, expected: str) -> None:
    joined = URL(base).join(URL(reference))
    assert str(joined) == expected
    assert URL(str(joined)) == joined
    assert str(URL(base).join(pickle.loads(pickle.dumps(URL(reference))))) == expected


@pytest.mark.parametrize(
    "url",
    [
        "non-special:\\\\opaque",
        "non-special://host/a\\b",
        "sc:\\../",
        "\\a",
        "#\\",
        "foo://h/a?b\\c",
        "http://h/a#d\\e",
    ],
)
def test_rfc_mode_rejects(url: str) -> None:
    with pytest.raises(ValueError, match="RFC 3986 does not allow"):
        URL(url, mode="rfc")


@pytest.mark.parametrize(
    ("scheme", "expected"),
    [
        # A special path reads "\\" as "/", so it is encoded there.
        ("http", "http://h/a%5Cb?c\\#d\\"),
        ("file", "file://h/a%5Cb?c\\#d\\"),
        ("bar", "bar://h/a\\b?c\\#d\\"),
    ],
)
def test_with_scheme(scheme: str, expected: str) -> None:
    url = URL("foo://h/a\\b?c\\#d\\").with_scheme(scheme)
    assert str(url) == expected
    assert url.path == "/a\\b"
    assert URL(str(url)) == url


def test_builders_whatwg() -> None:
    url = URL("http://h/")
    assert str(url.with_query({"a\\": "\\"})) == "http://h/?a\\=\\"
    assert str(url.with_query("a=\\")) == "http://h/?a=\\"
    assert str(url.extend_query(a="\\")) == "http://h/?a=\\"
    assert str(URL("http://h/?a=%5C").extend_query(b="\\")) == "http://h/?a=%5C&b=\\"
    assert str(url.update_query(a="\\")) == "http://h/?a=\\"
    assert str(url.with_fragment("\\")) == "http://h/#\\"
    built = URL.build(scheme="foo", host="h", path="/a\\b", query={"c": "\\"})
    assert str(built) == "foo://h/a%5Cb?c=\\"
    built = URL.build(scheme="http", host="h", query_string="c\\", fragment="d\\")
    assert str(built) == "http://h/?c\\#d\\"
    # A "%5C" written by the caller is a decoded value, not an escape.
    assert str(url.with_query(a="%5C")) == "http://h/?a=%255C"
    assert str(url.with_fragment("%5C")) == "http://h/#%255C"


def test_builders_rfc() -> None:
    url = URL("http://h/", mode="rfc")
    assert str(url.with_query(a="\\")) == "http://h/?a=%5C"
    assert str(url.extend_query(a="\\")) == "http://h/?a=%5C"
    assert str(url.update_query(a="\\")) == "http://h/?a=%5C"
    assert str(url.with_fragment("\\")) == "http://h/#%5C"
    built = URL.build(
        scheme="http", host="h", query_string="c\\", fragment="d\\", mode="rfc"
    )
    assert str(built) == "http://h/?c%5C#d%5C"


def test_human_repr_round_trip() -> None:
    url = URL.build(scheme="foo", host="h", path="/a\\b", query={"c": "\\"})
    url = url.with_fragment("\\")
    assert url.human_repr() == "foo://h/a%5Cb?c=\\#\\"
    assert URL(url.human_repr()) == url
