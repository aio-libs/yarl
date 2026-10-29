"""A "%" that does not start a "%XX" escape.

The WHATWG URL Standard keeps such a "%" as written in the path, the query
and the fragment (a validation error, not a failure). RFC 3986 does not allow
it, so RFC mode rejects it.
"""

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "expected", "path", "query_string", "fragment"),
    [
        (
            "http://example.com/foo/%2e%2",
            "http://example.com/foo/.%2",
            "/foo/.%2",
            "",
            "",
        ),
        ("http://example.com/foo%", "http://example.com/foo%", "/foo%", "", ""),
        ("http://example.com/foo%2", "http://example.com/foo%2", "/foo%2", "", ""),
        (
            "http://example.com/foo%2zbar",
            "http://example.com/foo%2zbar",
            "/foo%2zbar",
            "",
            "",
        ),
        (
            "http://example.com/foo%2Â©zbar",
            "http://example.com/foo%2%C3%82%C2%A9zbar",
            "/foo%2Â©zbar",
            "",
            "",
        ),
        ("wow:%NBD", "wow:%NBD", "%NBD", "", ""),
        ("wow:%1G", "wow:%1G", "%1G", "", ""),
        (
            "http://example.org/test?%GH",
            "http://example.org/test?%GH",
            "/test",
            "%GH",
            "",
        ),
        (
            "http://example.org/test?a#%GH",
            "http://example.org/test?a#%GH",
            "/test",
            "a",
            "%GH",
        ),
    ],
)
def test_whatwg_keeps_invalid_percent(
    url: str, expected: str, path: str, query_string: str, fragment: str
) -> None:
    parsed = URL(url)
    assert str(parsed) == expected
    assert parsed.path == path
    assert parsed.query_string == query_string
    assert parsed.fragment == fragment
    assert URL(expected) == parsed

    with pytest.raises(ValueError, match="not followed by two hexadecimal digits"):
        URL(url, mode="rfc")


def test_valid_escapes_unchanged() -> None:
    url = URL("http://example.com/%7e%2f%zz?%3d%GH#%41%")
    assert str(url) == "http://example.com/~%2F%zz?%3D%GH#A%"
    assert url.raw_path == "/~%2F%zz"
    assert url.path == "/~/%zz"
    assert url.query == {"=%GH": ""}


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://h/%4%31", "http://h/%4%31"),
        ("http://h/%%34%31", "http://h/%%341"),
        ("http://h/?%4%31", "http://h/?%4%31"),
        ("http://h/#%4%31", "http://h/#%4%31"),
    ],
)
def test_kept_percent_does_not_combine_with_decoded_digits(
    url: str, expected: str
) -> None:
    # Decoding "%31" after "%4" would make the new escape "%41"
    parsed = URL(url)
    assert str(parsed) == expected
    assert URL(expected) == parsed


def test_dot_segments() -> None:
    assert str(URL("http://example.com/a%/../b%")) == "http://example.com/b%"


def test_join() -> None:
    base = URL("http://example.com/a/b")
    assert str(base.join(URL("foo%"))) == "http://example.com/a/foo%"
    assert str(base.join(URL("../x%2zy"))) == "http://example.com/x%2zy"
    assert str(base.join(URL("?%GH"))) == "http://example.com/a/b?%GH"
    assert str(base.join(URL("#%GH"))) == "http://example.com/a/b#%GH"
    assert str(base.join(URL("http:/a/foo%"))) == "http://example.com/a/foo%"


def test_special_authority_path() -> None:
    assert str(URL("http:/a/foo%")) == "http://a/foo%"


def test_built_values_are_decoded() -> None:
    # A "%" in a value that is not encoded is a percent sign, so the
    # builders encode it as "%25" in both modes.
    url = URL.build(
        scheme="http", host="h", path="/p%", query_string="%GH", fragment="%GH"
    )
    assert str(url) == "http://h/p%25?%25GH#%25GH"
    assert url.path == "/p%"
    parsed = URL("http://h/foo%2z")
    assert str(parsed / "x%") == "http://h/foo%2z/x%25"
    assert str(parsed.with_path("/p%")) == "http://h/p%25"
    assert str(parsed.with_query("a=%GH")) == "http://h/foo%2z?a=%25GH"
    assert str(parsed.with_fragment("%GH")) == "http://h/foo%2z#%25GH"


def test_encoded_unchanged() -> None:
    url = URL.build(
        scheme="http",
        host="h",
        path="/p%",
        query_string="%GH",
        fragment="%GH",
        encoded=True,
        mode="rfc",
    )
    assert str(url) == "http://h/p%?%GH#%GH"
