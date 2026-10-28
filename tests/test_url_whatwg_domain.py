"""WHATWG mode keeps '"', "`", "{" and "}" in the host of a special URL.

The WHATWG URL Standard only rejects the forbidden domain code points in a
domain; RFC 3986 mode keeps to the reg-name grammar, which has none of them.
"""

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "host"),
    [
        ("http://!\"$&'()*+,-.;=_`{}~/", "!\"$&'()*+,-.;=_`{}~"),
        ("wss://!\"$&'()*+,-.;=_`{}~/", "!\"$&'()*+,-.;=_`{}~"),
        ('https://a"b/', 'a"b'),
        ("ftp://a`b/", "a`b"),
    ],
)
def test_parsed(url: str, host: str) -> None:
    parsed = URL(url)
    assert str(parsed) == url
    assert parsed.host == host
    assert URL(str(parsed)) == parsed
    with pytest.raises(ValueError, match="do not allow"):
        URL(url, mode="rfc")


def test_lowercased() -> None:
    assert str(URL("http://A{B}/")) == "http://a{b}/"


@pytest.mark.parametrize(
    ("url", "expected", "host"),
    [
        ("http://faß.A{b}/", "http://xn--fa-hia.a{b}/", "faß.a{b}"),
        ("http://faß。a{b}.ñ/", "http://xn--fa-hia.a{b}.xn--ida/", "faß.a{b}.ñ"),
        ("http://ñ{b}/", "http://xn--{b}-6ma/", "ñ{b}"),
        ("http://a｛b/", "http://a{b/", "a{b"),
        ("http://faß.a｛b｝/", "http://xn--fa-hia.a{b}/", "faß.a{b}"),
        ("http://Faß{B}.example/", "http://xn--fa{b}-mqa.example/", "faß{b}.example"),
        ("http://☃{b}.ß/", "http://xn--{b}-rm5a.xn--zca/", "☃{b}.ß"),
    ],
)
def test_non_ascii(url: str, expected: str, host: str) -> None:
    # UTS #46 maps the host and a label with "{" is encoded with Punycode,
    # so "faß" is not mapped to "fass" as the IDNA2003 fallback for the
    # whole host would do.
    parsed = URL(url)
    assert str(parsed) == expected
    assert parsed.host == host
    with pytest.raises(ValueError):
        URL(url, mode="rfc")


@pytest.mark.parametrize(
    ("url", "host"),
    [
        ("http://xn--fa{b}-mqa/", "faß{b}"),
        ("http://xn--fa{b}-mqa.xn--ida/", "faß{b}.ñ"),
        # Not Punycode, kept as written.
        ("http://xn--{b}/", "xn--{b}"),
    ],
)
def test_decoded_a_label(url: str, host: str) -> None:
    parsed = URL(url)
    assert str(parsed) == url
    assert parsed.host == host


@pytest.mark.parametrize(
    "url",
    [
        # A noncharacter, which UTS #46 and IDNA2003 reject.
        "http://a\ufdd0{b}/",
        # Left-to-right and right-to-left letters in one label.
        "http://x{\u05d0}/",
        "http://x{\u05d0}.com/",
        # A right-to-left label must not end with "}".
        "http://\u05d0{\u05d1}/",
        # A label must not start with a combining mark.
        "http://\u0301{b}/",
        "http://a.\u0301{b}/",
    ],
)
def test_invalid_label(url: str) -> None:
    with pytest.raises(ValueError):
        URL(url)


def test_bidi_label() -> None:
    # A left-to-right label next to a right-to-left one.
    assert str(URL("http://1{a}.\u05d0/")) == "http://1{a}.xn--4db/"


@pytest.mark.parametrize("char", "^|<> %")
def test_forbidden_domain_code_point_parsed(char: str) -> None:
    with pytest.raises(ValueError):
        URL(f"http://a{{{char}}}/")


@pytest.mark.parametrize("char", "\x00\t\n\r #%/:<>?@[\\]^|\x7f")
def test_forbidden_domain_code_point_with_host(char: str) -> None:
    with pytest.raises(ValueError, match="cannot contain"):
        URL("http://example.com/").with_host(f"a{{{char}}}")


@pytest.mark.parametrize("url", ["http://a{b}%7C/", "http://a{b}.1/"])
def test_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        URL(url)


def test_build() -> None:
    assert str(URL.build(scheme="http", host="A{b}")) == "http://a{b}"
    assert str(URL.build(scheme="http", authority="u@a{b}:1")) == "http://u@a{b}:1"
    with pytest.raises(ValueError, match=r"cannot contain '\{' \(at position 1\)"):
        URL.build(scheme="http", host="a{b}", mode="rfc")


def test_with_host() -> None:
    assert str(URL("http://example.com/p").with_host('A"b')) == 'http://a"b/p'
    with pytest.raises(ValueError, match="cannot contain '\"'"):
        URL("http://example.com/p", mode="rfc").with_host('a"b')


def test_with_host_non_ascii_rfc() -> None:
    with pytest.raises(ValueError, match=r"cannot contain '\{' \(at position 5\)"):
        URL("http://example.com/p", mode="rfc").with_host("faß.a{b}")


def test_with_scheme() -> None:
    assert str(URL("sc://faß.A{b}/").with_scheme("https")) == "https://xn--fa-hia.a{b}/"


def test_join() -> None:
    assert str(URL("http://example.com/a").join(URL("//a`b/c"))) == "http://a`b/c"
    with pytest.raises(ValueError):
        URL("//a`b/c", mode="rfc")
