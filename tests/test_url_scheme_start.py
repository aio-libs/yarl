"""A scheme starts with a letter, as RFC 3986 section 3.1 and WHATWG do.

RFC 3986 section 3.1 writes ``scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" /
"." )`` and the WHATWG "scheme start state" takes an ASCII alpha in that
first position too. urllib's ``scheme_chars``, which the parser used for the
first character as well, also holds the digits and the signs, so a string
such as ``10.0.0.7:8080/foo.html`` was read as a URL with the scheme
``10.0.0.7`` instead of a relative reference.
"""

import pytest

from yarl import URL


@pytest.mark.parametrize(
    "url",
    [
        "10.0.0.7:8080/foo.html",
        "127.0.0.1:8080/x",
        "1a:b",
        "1:1",
        "+1:b",
        "-1:b",
        ".1:b",
        "1abc://example.com/x?q#f",
    ],
)
def test_prefix_without_a_letter_is_not_a_scheme(url: str) -> None:
    parsed = URL(url)
    assert parsed.scheme == ""
    assert parsed.raw_host is None
    # The string is unchanged, it is a relative path rather than a scheme,
    # a host and a path.
    assert str(parsed) == url
    assert URL(str(parsed)) == parsed
    assert URL(url, encoded=True).scheme == ""
    # RFC 3986 mode reads the prefix as a scheme too, and rejects it.
    with pytest.raises(ValueError, match="is not a valid scheme"):
        URL(url, mode="rfc")


@pytest.mark.parametrize(
    ("url", "scheme", "raw_host"),
    [
        ("a:b", "a", None),
        ("a+b-c.d://h/p", "a+b-c.d", "h"),
        ("HTTP://h/p", "http", "h"),
    ],
)
def test_prefix_with_a_letter_is_a_scheme(
    url: str, scheme: str, raw_host: str | None
) -> None:
    parsed = URL(url)
    assert parsed.scheme == scheme
    assert parsed.raw_host == raw_host


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        ("http://example.com/a/b", "http://example.com/a/10.0.0.7:8080/foo.html"),
        ("http://h/", "http://h/10.0.0.7:8080/foo.html"),
        ("sc:sd", "sc:10.0.0.7:8080/foo.html"),
        # The vendored web-platform-tests corpus expects this one, see
        # tools/conformance/wpt/urltestdata.json.
        ("file:///some/dir/bar.html", "file:///some/dir/10.0.0.7:8080/foo.html"),
    ],
)
def test_join_keeps_the_base(base: str, expected: str) -> None:
    joined = URL(base).join(URL("10.0.0.7:8080/foo.html"))
    assert str(joined) == expected
    assert joined == URL(expected)


@pytest.mark.parametrize(
    ("path", "raw_path"),
    [
        # A ":" that would read back as a scheme is encoded.
        ("a:b", "a%3Ab"),
        ("a:b:c", "a%3Ab:c"),
        # A prefix that is no scheme is kept as it is.
        ("1a:b", "1a:b"),
        (":b", ":b"),
        ("/:b", "/:b"),
        ("a_b:c", "a_b:c"),
    ],
)
def test_built_relative_path(path: str, raw_path: str) -> None:
    built = URL.build(path=path)
    assert built.raw_path == raw_path
    assert URL(str(built)) == built


def test_backslash_in_a_reference() -> None:
    # "\\" is read as "/" in a reference only when it is joined with a
    # special base, see _backslashes(); the scheme check that tells a
    # reference from a URL takes the same first letter as the parser.
    reference = URL("1abc://example.com/\\x")
    assert reference.scheme == ""
    assert str(reference) == "1abc://example.com/%5Cx"
    assert str(URL("http://h/").join(reference)) == "http://h/1abc://example.com//x"
    assert str(URL("sc://h/").join(reference)) == "sc://h/1abc://example.com/%5Cx"
