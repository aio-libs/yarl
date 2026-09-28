"""Conformance tests for RFC 3986 (STD 66), URI Generic Syntax.

https://www.rfc-editor.org/rfc/rfc3986

Section references are to RFC 3986 unless stated otherwise.  The
reference resolution examples of section 5.4 are covered by the
``NORMAL`` and ``ABNORMAL`` tables in ``tests/test_url.py``.

Cases where yarl knowingly deviates from the RFC are marked as strict
xfails whose reason starts with ``yarl:``, so the suite documents each
divergence and flags it once the behaviour changes.
"""

import pytest

from yarl import URL
from yarl._path import normalize_path


def diverges(reason: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(strict=True, reason=f"yarl: {reason}")


# Section 1.1.2 and section 3 examples, decomposed into
# (scheme, user, host, port, path, query, fragment).
COMPONENTS = [
    (
        "foo://example.com:8042/over/there?name=ferret#nose",
        ("foo", None, "example.com", 8042, "/over/there", "name=ferret", "nose"),
    ),
    (
        "ftp://ftp.is.co.za/rfc/rfc1808.txt",
        ("ftp", None, "ftp.is.co.za", None, "/rfc/rfc1808.txt", "", ""),
    ),
    (
        "http://www.ietf.org/rfc/rfc2396.txt",
        ("http", None, "www.ietf.org", None, "/rfc/rfc2396.txt", "", ""),
    ),
    (
        "ldap://[2001:db8::7]/c=GB?objectClass?one",
        ("ldap", None, "2001:db8::7", None, "/c=GB", "objectClass?one", ""),
    ),
    (
        "mailto:John.Doe@example.com",
        ("mailto", None, None, None, "John.Doe@example.com", "", ""),
    ),
    (
        "news:comp.infosystems.www.servers.unix",
        ("news", None, None, None, "comp.infosystems.www.servers.unix", "", ""),
    ),
    (
        "tel:+1-816-555-1212",
        ("tel", None, None, None, "+1-816-555-1212", "", ""),
    ),
    (
        "telnet://192.0.2.16:80/",
        ("telnet", None, "192.0.2.16", 80, "/", "", ""),
    ),
    (
        "urn:oasis:names:specification:docbook:dtd:xml:4.1.2",
        (
            "urn",
            None,
            None,
            None,
            "oasis:names:specification:docbook:dtd:xml:4.1.2",
            "",
            "",
        ),
    ),
    (
        "foo://user@example.com/",
        ("foo", "user", "example.com", None, "/", "", ""),
    ),
]


@pytest.mark.parametrize(
    ("url", "expected"), COMPONENTS, ids=[c[0] for c in COMPONENTS]
)
def test_components(url: str, expected: tuple[object, ...]) -> None:
    u = URL(url)
    assert (
        u.scheme,
        u.raw_user,
        u.raw_host,
        u.explicit_port,
        u.raw_path,
        u.raw_query_string,
        u.raw_fragment,
    ) == expected
    assert str(u) == url


# Section 3.1: schemes are case-insensitive, canonical form is lowercase.
@pytest.mark.parametrize(
    ("url", "scheme"),
    [
        ("HTTP://example.com/", "http"),
        ("hTtP://example.com/", "http"),
        ("a+b-c.d://example.com/", "a+b-c.d"),
        ("A0://example.com/", "a0"),
    ],
)
def test_scheme(url: str, scheme: str) -> None:
    assert URL(url).scheme == scheme


# URI references that must round-trip unchanged: each is valid under the
# ABNF of Appendix A and already in normal form.
VALID = [
    pytest.param("foo:/a/b", id="3.3-path-absolute"),
    pytest.param("foo:a/b", id="3.3-path-rootless"),
    pytest.param("foo:", id="3.3-path-empty"),
    pytest.param("http://example.com/a//b/", id="3.3-empty-segments"),
    pytest.param("http://example.com/!$&'()*+,;=:@", id="3.3-pchar-sub-delims"),
    pytest.param("http://example.com/?a/b?c", id="3.4-query-slash-question"),
    pytest.param("http://example.com/#a/b?c", id="3.5-fragment-slash-question"),
    pytest.param("http://!$&'()*+,;=@example.com/", id="3.2.1-userinfo-sub-delims"),
    pytest.param("http://256.1.1.1/", id="3.2.2-reg-name-not-ipv4"),
    pytest.param("http://1.2.3.04/", id="3.2.2-reg-name-leading-zero"),
    pytest.param("http://0x7f.1/", id="3.2.2-reg-name-hex"),
    pytest.param("http://127.1/", id="3.2.2-reg-name-short"),
    pytest.param(
        "http://%C3%A9.example/",
        id="3.2.2-reg-name-pct",
        marks=diverges("host lowercasing also lowercases percent-encodings"),
    ),
    pytest.param("./a:b", id="4.2-colon-behind-dot-segment"),
    pytest.param("//example.com/p", id="4.2-network-path"),
    pytest.param("?q", id="4.2-query-only"),
    pytest.param("#f", id="4.2-fragment-only"),
    pytest.param(
        "http://[v1.fe]/",
        id="3.2.2-ipvfuture",
        marks=diverges("IPvFuture literal loses its brackets"),
    ),
    pytest.param(
        "foo:///a",
        id="3.2-empty-authority",
        marks=diverges("empty authority dropped for schemes outside uses_netloc"),
    ),
    pytest.param(
        "http://example.com/p?",
        id="6.2.3-empty-query-kept",
        marks=diverges("empty query delimiter dropped"),
    ),
    pytest.param(
        "http://example.com/p#",
        id="6.2.3-empty-fragment-kept",
        marks=diverges("empty fragment delimiter dropped"),
    ),
    pytest.param(
        "http://u:p:q@example.com/",
        id="3.2.1-colon-in-password",
        marks=diverges("':' in the password is percent-encoded"),
    ),
    pytest.param(
        "http://example.com:65536/",
        id="3.2.3-port-no-upper-bound",
        marks=diverges("ports above 65535 are rejected, port = *DIGIT"),
    ),
]


@pytest.mark.parametrize("url", VALID)
def test_valid_reference_round_trips(url: str) -> None:
    assert str(URL(url)) == url


# Strings that do not match URI-reference in Appendix A.
INVALID = [
    pytest.param("http://[::1/", id="3.2.2-unclosed-ip-literal"),
    pytest.param("http://::1/", id="3.2.2-ipv6-without-brackets"),
    pytest.param("http://example.com:8a/", id="3.2.3-port-not-digits"),
    pytest.param("http://example.com:-1/", id="3.2.3-port-negative"),
    pytest.param("https://[0::0::0]/", id="3.2.2-two-double-colons"),
    pytest.param("http://[:]/", id="3.2.2-lone-colon"),
    pytest.param(
        "1abc://example.com/",
        id="3.1-scheme-starts-with-digit",
        marks=diverges("scheme starting with a digit is accepted"),
    ),
    pytest.param(
        "://example.com",
        id="4.2-colon-in-first-segment",
        marks=diverges("relative path with ':' in the first segment is accepted"),
    ),
    pytest.param("http://exa mple.com/", id="3.2.2-space-in-host"),
    pytest.param("http://exa<mple.com/", id="3.2.2-lt-in-host"),
    pytest.param("http://example.com:+80/", id="3.2.3-port-plus-sign"),
    pytest.param("http://example.com: 80/", id="3.2.3-port-space"),
]


@pytest.mark.parametrize("url", INVALID)
def test_invalid_reference_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        URL(url)


# Section 2.1: characters outside the URI grammar must be percent-encoded.
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://example.com/a b", "http://example.com/a%20b"),
        (
            'http://example.com/"<>\\^`{|}[]',
            "http://example.com/%22%3C%3E%5C%5E%60%7B%7C%7D%5B%5D",
        ),
        (
            'http://example.com/?"<>\\^`{|}[]',
            "http://example.com/?%22%3C%3E%5C%5E%60%7B%7C%7D%5B%5D",
        ),
        (
            'http://example.com/#"<>\\^`{|}[]',
            "http://example.com/#%22%3C%3E%5C%5E%60%7B%7C%7D%5B%5D",
        ),
        ("http://example.com/\u00e9", "http://example.com/%C3%A9"),
    ],
)
def test_disallowed_characters_encoded(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


PCT_TEMPLATES = {
    "user": "http://{}@example.com/",
    "path": "http://example.com/{}",
    "query": "http://example.com/?{}",
    "fragment": "http://example.com/#{}",
}


# Sections 2.3 and 6.2.2.2: percent-encoded unreserved characters are
# equivalent to the characters themselves and should be decoded.
@pytest.mark.parametrize("component", PCT_TEMPLATES)
def test_unreserved_percent_encoding_decoded(component: str) -> None:
    template = PCT_TEMPLATES[component]
    assert str(URL(template.format("%41%7a%30%2d%2E%5f%7E"))) == template.format(
        "Az0-._~"
    )


# Sections 2.1 and 6.2.2.1: hex digits of percent-encodings are
# case-insensitive and should be normalized to uppercase.
@pytest.mark.parametrize("component", PCT_TEMPLATES)
def test_percent_encoding_uppercased(component: str) -> None:
    template = PCT_TEMPLATES[component]
    assert str(URL(template.format("%c3%a9%5b"))) == template.format("%C3%A9%5B")


# Sections 2.2 and 6.2.2.2: a percent-encoded reserved character is not
# equivalent to the character itself and must be kept encoded.
RESERVED = ":/?#[]@!$&'()*+,;="
# Reserved characters that yarl decodes in each component.
RESERVED_DECODED = {
    "user": "!$&'()*+,;=",
    "path": ":@!$&'()*,;=",
    "query": ":/?@!$'()*,",
    "fragment": ":/?@!$&'()*+,;=",
}
RESERVED_CASES = [
    pytest.param(
        component,
        char,
        id=f"{component}-%{ord(char):02X}",
        marks=(
            [diverges(f"%{ord(char):02X} is decoded in the {component}")]
            if char in RESERVED_DECODED[component]
            else []
        ),
    )
    for component in PCT_TEMPLATES
    for char in RESERVED
]


@pytest.mark.parametrize(("component", "char"), RESERVED_CASES)
def test_reserved_percent_encoding_preserved(component: str, char: str) -> None:
    encoded = f"a%{ord(char):02X}b"
    template = PCT_TEMPLATES[component]
    assert str(URL(template.format(encoded))) == template.format(encoded)


# Section 3.2.2: reg-name is case-insensitive, IP-literals are unchanged.
@pytest.mark.parametrize(
    ("url", "host"),
    [
        ("http://ExAmPlE.CoM/", "example.com"),
        ("http://1.2.3.4/", "1.2.3.4"),
        ("http://[2001:DB8::7]/", "2001:db8::7"),
        pytest.param(
            "http://ex%41mple.com/",
            "example.com",
            marks=diverges("percent-encoded unreserved octets in host kept"),
        ),
        pytest.param(
            "http://EX%4Ample.com/",
            "example.com",
            marks=diverges("host lowercasing also lowercases percent-encodings"),
        ),
    ],
)
def test_host_normalization(url: str, host: str) -> None:
    assert URL(url).raw_host == host


# Section 3.2.3: the port may be empty and may carry leading zeros.
@pytest.mark.parametrize(
    ("url", "port"),
    [
        ("http://example.com:/", None),
        ("http://example.com:8080/", 8080),
        ("http://example.com:008080/", 8080),
        ("foo://example.com:0/", 0),
    ],
)
def test_port(url: str, port: int | None) -> None:
    assert URL(url).explicit_port == port


# Section 3.3: without an authority a path cannot begin with "//", so
# serialization must keep it distinguishable from an authority.
def test_path_starting_with_double_slash_without_authority() -> None:
    url = URL.build(scheme="foo", path="//a")
    assert URL(str(url)).raw_path == "//a"


# Section 4.2: a relative-path reference whose first segment contains ':'
# would be mistaken for a scheme and must be written differently.
def test_relative_path_first_segment_colon() -> None:
    url = URL.build(path="a:b")
    assert not URL(str(url)).scheme
    assert URL(str(url)).path == "a:b"


# Section 5.2.4 worked examples of remove_dot_segments.
@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/a/b/c/./../../g", "/a/g"),
        ("mid/content=5/../6", "mid/6"),
    ],
)
def test_remove_dot_segments(path: str, expected: str) -> None:
    assert normalize_path(path) == expected


# Section 5.4.2: "http:g" resolves to "http:g" in strict parsers; the
# backward-compatible variant yarl implements is explicitly permitted.
def test_join_same_scheme_backward_compatible() -> None:
    assert str(URL("http://a/b/c/d;p?q").join(URL("http:g"))) == "http://a/b/c/g"


# Section 5.2.2: components of the target URI.
@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        pytest.param("http://a/b?q#f", "#g", "http://a/b?q#g", id="fragment"),
        pytest.param("http://a/b?q#f", "g", "http://a/g", id="path"),
        pytest.param(
            "http://a/b?q#f",
            "?y",
            "http://a/b?y",
            id="query-drops-base-fragment",
            marks=diverges("base fragment kept"),
        ),
        pytest.param(
            "http://a/b?q#f",
            "",
            "http://a/b?q",
            id="empty-drops-base-fragment",
            marks=diverges("base fragment kept"),
        ),
        pytest.param(
            "file://host/",
            "file:///C:/",
            "file:///C:/",
            id="empty-authority-defined",
            marks=diverges("empty reference authority replaced by the base host"),
        ),
        pytest.param(
            "http://a/b/c/%2F/d",
            "x",
            "http://a/b/c/%2F/x",
            id="merge-keeps-encoded-slash",
            marks=diverges("merge uses decoded base segments"),
        ),
        pytest.param(
            "http://a/b%2Fc/d",
            "e",
            "http://a/b%2Fc/e",
            id="merge-keeps-encoded-slash-in-segment",
            marks=diverges("merge uses decoded base segments"),
        ),
    ],
)
def test_join_target_components(base: str, reference: str, expected: str) -> None:
    assert str(URL(base).join(URL(reference))) == expected


# Section 5.2: reference resolution is independent of the scheme.
@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        ("ws://a/b/c", "d", "ws://a/b/d"),
        pytest.param(
            "foo://a/b/c",
            "../d",
            "foo://a/d",
            marks=diverges("join only resolves schemes listed in uses_relative"),
        ),
        pytest.param(
            "foo:/a/b",
            "c",
            "foo:/a/c",
            marks=diverges("join only resolves schemes listed in uses_relative"),
        ),
        pytest.param(
            "foo:a/b",
            "c",
            "foo:a/c",
            marks=diverges("join only resolves schemes listed in uses_relative"),
        ),
        pytest.param(
            "urn:example:a",
            "#f",
            "urn:example:a#f",
            marks=diverges("join only resolves schemes listed in uses_relative"),
        ),
    ],
)
def test_join_scheme_independent(base: str, reference: str, expected: str) -> None:
    assert str(URL(base).join(URL(reference))) == expected


# Section 6.2: equivalent URIs after syntax-based and scheme-based
# normalization.
@pytest.mark.parametrize(
    ("first", "second"),
    [
        pytest.param(
            "eXAMPLE://a/./b/../b/%63/%7bfoo%7d",
            "example://a/b/c/%7Bfoo%7D",
            id="6.2.2",
        ),
        pytest.param(
            "HTTP://www.EXAMPLE.com/", "http://www.example.com/", id="6.2.2.1-case"
        ),
        pytest.param("http://example.com/%7e", "http://example.com/~", id="6.2.2.2"),
        pytest.param(
            "http://example.com/a/%2e%2E/b", "http://example.com/b", id="6.2.2.3"
        ),
        pytest.param("http://example.com", "http://example.com/", id="6.2.3-path"),
        pytest.param("http://example.com:/", "http://example.com/", id="6.2.3-port"),
        pytest.param(
            "http://example.com:80/",
            "http://example.com/",
            id="6.2.3-default-port",
            marks=diverges("explicit default port makes URLs compare unequal"),
        ),
        pytest.param(
            "http://ex%41mple.com/",
            "http://example.com/",
            id="6.2.2.2-host",
            marks=diverges("percent-encoded unreserved octets in host kept"),
        ),
    ],
)
def test_equivalent(first: str, second: str) -> None:
    assert URL(first) == URL(second)


# Section 2.2: replacing a reserved character by its percent-encoding
# produces a different URI.
@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("http://example.com/a%2Fb", "http://example.com/a/b"),
        ("http://example.com/?a%26b", "http://example.com/?a&b"),
        pytest.param(
            "http://example.com/a%3Bb",
            "http://example.com/a;b",
            marks=diverges("%3B is decoded in the path"),
        ),
    ],
)
def test_not_equivalent(first: str, second: str) -> None:
    assert URL(first) != URL(second)
