"""RFC 3986 mode rejects URL strings outside the RFC 3986 and RFC 3987 grammar.

RFC 3986 mode takes IRIs (RFC 3987): non-ASCII characters are
percent-encoded as UTF-8, a non-ASCII host is encoded with IDNA2008. Other
characters outside the grammar, which WHATWG mode percent-encodes or
removes, make the string invalid. Only parsing an unencoded string is
checked: built components are decoded values, and ``encoded=True`` trusts
the caller.
"""

import pytest

from yarl import URL, Mode


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "http://\xe9@example.com/\u4f60\u597d?q=\U0001f525#\u03b2",
            "http://%C3%A9@example.com/%E4%BD%A0%E5%A5%BD?q=%F0%9F%94%A5#%CE%B2",
        ),
        ("http://\xe9.example/", "http://xn--9ca.example/"),
        # Private use is allowed in the query only.
        ("http://example.com/?\ue000", "http://example.com/?%EE%80%80"),
        # Every ASCII character that the grammar allows outside the host.
        (
            "http://u!$&'()*+,;=:p@h/-._~!$&'()*+,;=:@/?-._~/?#-._~/?",
            "http://u!$&'()*+,;=:p@h/-._~!$&'()*+,;=:@/?-._~/?#-._~/?",
        ),
        ("http://example.com/%41%c3%a9", "http://example.com/A%C3%A9"),
        ("http://[fe80::1%25eth0]/", "http://[fe80::1%25eth0]/"),
        ("./a:b", "./a:b"),
        ("urn:isbn:0451450523", "urn:isbn:0451450523"),
    ],
)
def test_iri_accepted(url: str, expected: str) -> None:
    assert str(URL(url, mode="rfc")) == expected


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("http://a b@example.com/", "' ' in the userinfo"),
        ("http://a%zz@example.com/", "two hexadecimal digits in the userinfo"),
        ("http://exa mple.com/", "' ' in the host"),
        ("http://exa<mple.com/", "'<' in the host"),
        ("http://[fe80::1%25a b]/", "' ' in the host"),
        ("http://[fe80::1%]/", "two hexadecimal digits in the host"),
        ("http://[fe80::1%eth0]/", "two hexadecimal digits in the host"),
        ("http://a%2/", "two hexadecimal digits in the host"),
        ("http://f:\n/c", "'\\\\n' in the port"),
        ("http://h:%31/", "'%' in the port"),
        ("http://[::1]:8a/", "'a' in the port"),
        ("http://example.com/a b", "' ' in the path"),
        ('http://example.com/"', "'\"' in the path"),
        ("http://example.com/[]", "'\\[' in the path"),
        ("http://example.com/%", "two hexadecimal digits in the path"),
        ("http://example.com/%GH", "two hexadecimal digits in the path"),
        ("http://example.com/\ue000", "'\\\\ue000' in the path"),
        ("http://example.com/?<", "'<' in the query"),
        ("http://example.com/?%1", "two hexadecimal digits in the query"),
        ("http://example.com/#a#b", "'#' in the fragment"),
        ("http://example.com/#\ue000", "'\\\\ue000' in the fragment"),
        ("http://example.com/#^`{|}", "'\\^' in the fragment"),
        # Code points outside the IRI grammar, and bidi formatting.
        ("http://example.com/\uffff", "'\\\\uffff' in the path"),
        ("http://example.com/\x80", "'\\\\x80' in the path"),
        ("http://example.com/\u202e", "'\\\\u202e' in the path"),
        ("http://example.com/\u200e", "'\\\\u200e' in the path"),
        # Tabs, newlines, controls and spaces are not removed.
        ("http://example.com/a\tb", "'\\\\t' in the path"),
        ("http://exam\nple.com/", "'\\\\n' in the host"),
        ("http://example.com/\x00", "'\\\\x00' in the path"),
        ("http://example.com/ ", "' ' in the path"),
        (" http://example.com/", "' http' is not a valid scheme"),
        ("1abc://example.com/", "'1abc' is not a valid scheme"),
        ("10.0.0.7:8080/foo.html", "'10.0.0.7' is not a valid scheme"),
        # RFC 3986 section 4.2.
        (":foo.com/", "first segment of a relative path cannot contain ':'"),
        ("://example.com", "first segment of a relative path cannot contain ':'"),
        # The messages of earlier checks stay.
        ("http://example.com/a\\b", "RFC 3986 does not allow '\\\\'"),
        ("sc://a@b@c/", "userinfo cannot contain '@'"),
    ],
)
def test_outside_grammar_rejected(url: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        URL(url, mode="rfc")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://example.com/a b", "http://example.com/a%20b"),
        ("http://example.com/#a#b", "http://example.com/#a%23b"),
        ("http://example.com/%zz", "http://example.com/%25zz"),
        (" http://example.com/a\tb ", "http://example.com/ab"),
    ],
)
def test_whatwg_mode_unchanged(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


def test_encoded_unchanged() -> None:
    assert str(URL("http://example.com/a b", encoded=True, mode="rfc")) == (
        "http://example.com/a b"
    )


def test_built_components_encoded() -> None:
    url = URL.build(
        scheme="http",
        user="a b",
        host="example.com",
        path="/a b",
        query={"q": "<>"},
        fragment="a#b",
        mode="rfc",
    )
    assert str(url) == "http://a%20b@example.com/a%20b?q=%3C%3E#a%23b"
    base = URL("http://example.com/", mode="rfc")
    assert str(base.with_path("a b")) == "http://example.com/a%20b"
    assert str(base / "a b") == "http://example.com/a%20b"
    assert str(base.joinpath("\xe9")) == "http://example.com/%C3%A9"
    assert str(base.with_query(q="a b")) == "http://example.com/?q=a+b"
    assert str(base.with_fragment("a#b")) == "http://example.com/#a%23b"


# RFC 3986 section 4.2: a relative path has no ":" in its first segment, so
# a built one is encoded to parse back in RFC 3986 mode. WHATWG mode only
# encodes a ":" that would read as a scheme.
@pytest.mark.parametrize(
    ("path", "whatwg", "rfc"),
    [
        (":foo", ":foo", "%3Afoo"),
        (":a/b:c", ":a/b:c", "%3Aa/b:c"),
        ("a:b", "a%3Ab", "a%3Ab"),
        ("\u00e9:x", "%C3%A9:x", "%C3%A9%3Ax"),
    ],
)
def test_built_relative_colon(path: str, whatwg: str, rfc: str) -> None:
    for mode, expected in ((Mode.WHATWG, whatwg), (Mode.RFC, rfc)):
        url = URL.build(path=path, mode=mode)
        assert str(url) == expected
        assert url.path == path
        assert URL(str(url), mode=mode) == url


def test_relative_colon_on_mode_change() -> None:
    url = URL(URL.build(path=":foo"), mode="rfc")
    assert str(url) == "%3Afoo"
    assert url.human_repr() == "%3Afoo"
    assert URL.build(path=":foo").human_repr() == ":foo"
