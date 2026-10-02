"""WHATWG mode percent-decodes the host of a special URL."""

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://ex%41mple.com/", "http://example.com/"),
        ("https://%e2%98%83/", "https://xn--n3h/"),
        ("ws://u@%C3%B1.test:81/p", "ws://u@xn--ida.test:81/p"),
        ("http://%c3%b1%41.test/", "http://xn--a-qga.test/"),
        ("http://ñ%41.test/", "http://xn--a-qga.test/"),
        ("file://%41/p", "file://a/p"),
        ("http://%30x7f.1/", "http://127.0.0.1/"),
        ("http://127.0.0.1%31/", "http://127.0.0.11/"),
    ],
)
def test_decoded(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


@pytest.mark.parametrize(
    "url",
    [
        # Forbidden domain code points and C0 controls.
        "http://ho%00st/",
        "http://ho%20st/",
        "http://ho%2Fst/",
        "http://ho%3Ast/",
        "http://ho%40st/",
        "http://ho%7Cst/",
        "http://%25/",
        "http://%2541/",
        # Not in the RFC 3986 reg-name, which yarl keeps to.
        "http://ho%22st/",
        # Invalid UTF-8 decodes to U+FFFD, which IDNA rejects.
        "https://example.com%80/",
        # A noncharacter.
        "http://%ef%b7%90zyx.com/",
        # Fullwidth "%41", which IDNA maps to "%41".
        "http://%ef%bc%85%ef%bc%94%ef%bc%91.com/",
        # A default-ignorable code point, rejected by yarl as in a raw host.
        "https://a%C2%ADb/",
        # Not an IPv4 address once decoded.
        "http://foo.%31/",
        # An IPv4 address followed by "%", which is not a zone identifier.
        "http://127.0.0.1%00/",
        "http://127.0.0.1%25eth0/",
    ],
)
def test_rejected(url: str) -> None:
    with pytest.raises(ValueError, match="once percent-decoded"):
        URL(url)
    # RFC 3986 mode keeps the percent-encoding.
    assert URL(url, mode="rfc").raw_host


@pytest.mark.parametrize("url", ["sc://ex%41mple.com/", "sc://ho%00st/"])
def test_non_special_scheme(url: str) -> None:
    assert str(URL(url)) == url


def test_rfc_mode() -> None:
    url = URL("http://ex%41mple.com/", mode="rfc")
    assert url.raw_host == "ex%41mple.com"


def test_build_fullwidth_percent() -> None:
    with pytest.raises(ValueError, match="once percent-decoded"):
        URL.build(scheme="http", host="％４１.com")


def test_build_ipv4_zone() -> None:
    with pytest.raises(ValueError, match="once percent-decoded"):
        URL.build(scheme="http", host="127.0.0.1%00")
    url = URL.build(scheme="http", host="127.0.0.1%00", mode="rfc")
    assert url.raw_host == "127.0.0.1%00"
    assert URL.build(scheme="sc", host="127.0.0.1%00").raw_host == "127.0.0.1%00"


@pytest.mark.parametrize("host", ["127.0.0.1%::", "1.2.3.4%x@9", "127.0.0.1%25::"])
def test_build_ipv4_suffix_invalid_reg_name(host: str) -> None:
    """An IPv4 address with a "%" suffix must be a valid reg-name.

    The suffix is percent-encoding in the host, so a ":" or a bare "%" in it
    makes a netloc that ``split_netloc`` cannot parse back; the validating
    entry points must reject it instead of building a URL whose ``raw_host``
    then raises (RFC 3986 mode and non-special schemes skip the WHATWG
    host decode that caught this for special schemes).
    """
    for build in (
        lambda: URL.build(scheme="http", host=host, mode="rfc"),
        lambda: URL.build(scheme="sc", host=host),
        lambda: URL("sc://example.com/").with_host(host),
        lambda: URL("http://example.com/", mode="rfc").with_host(host),
    ):
        with pytest.raises(ValueError, match="cannot contain"):
            build()


def test_build_ipv4_suffix_valid_pct_encoding() -> None:
    """Valid percent-encoding in an IPv4 suffix is kept, any hex case."""
    assert URL.build(scheme="sc", host="1.2.3.4%2F9").raw_host == "1.2.3.4%2F9"
    assert URL.build(scheme="sc", host="127.0.0.1%250").raw_host == "127.0.0.1%250"


def test_build_non_ascii() -> None:
    url = URL.build(scheme="http", host="ñ%41")
    assert url.raw_host == "xn--a-qga"


def test_with_scheme() -> None:
    url = URL("sc://ex%41mple.com/p").with_scheme("http")
    assert str(url) == "http://example.com/p"
    with pytest.raises(ValueError, match="once percent-decoded"):
        URL("sc://ho%00st/p").with_scheme("http")


def test_join() -> None:
    url = URL("http://example.com/").join(URL("//ex%41mple.org/p"))
    assert str(url) == "http://example.org/p"
    url = URL("http://example.com/", mode="rfc").join(URL("//ex%41mple.org/p"))
    assert url.raw_host == "ex%41mple.org"


def test_mode_change() -> None:
    url = URL(URL("http://ex%41mple.com/", mode="rfc"), mode="whatwg")
    assert str(url) == "http://example.com/"
    with pytest.raises(ValueError, match="once percent-decoded"):
        URL(URL("http://ho%00st/", mode="rfc"), mode="whatwg")


def test_encoded() -> None:
    # A pre-encoded URL is taken as is.
    assert URL("http://ex%41mple.com/", encoded=True).raw_host == "ex%41mple.com"
