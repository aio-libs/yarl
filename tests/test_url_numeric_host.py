"""Hosts of special schemes that end in a number are IPv4 addresses.

The WHATWG URL Standard parses such a host, like "0x7f.1" or "foo.123", as
an IPv4 address: it serializes it as a dotted quad, or rejects it when a
label is not a number ("foo") or a number is out of range. yarl follows
that in WHATWG mode; RFC 3986 mode accepts all of them as a reg-name.
"""

import pytest

from yarl import URL


@pytest.mark.parametrize(
    "url",
    [
        "http://💩.123/",
        "http://foo.123/",
        "http://foo.123./",
        "https://foo.0x/",
        "ws://foo.09/",
        "wss://foo.0x1f/",
        "ftp://foo.bar.1/",
        "file://foo.1/x",
        "http://..123/",
        "http://1..2/",
        "http://4294967296/",
        "http://0x100000000/",
        "http://256.256.256.256/",
        "http://256.0.0.1/",
        "http://1.256.0.1/",
        "http://1.2.3.4.5/",
        "http://1.2.3.4.5./",
        "http://1.2.3.08/",
        "http://09.2.3.4/",
        "http://0x100.2.3.4/",
        "http://0xg.1/",
        "http://1.2.65536/",
        "http://1.16777216/",
        "http://12345678901234567890123456789012345678901234567890/",
    ],
)
def test_rejected(url: str) -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://foo.123/",
        "https://foo.0x/",
        "ws://foo.09/",
        "http://256/",
        "http://0x7f.1/",
        "http://1.2.3.4./",
        "http://4294967296/",
    ],
)
def test_accepted_in_rfc_mode(url: str) -> None:
    # RFC 3986 treats these hosts as a plain reg-name.
    assert str(URL(url, mode="rfc")) == url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://1.2.3.4/", "http://1.2.3.4/"),
        ("http://1.2.3.4./", "http://1.2.3.4/"),
        ("http://1.2.3/", "http://1.2.0.3/"),
        ("http://0x7f.1/", "http://127.0.0.1/"),
        ("http://0X7F.1/", "http://127.0.0.1/"),
        ("http://0x.1/", "http://0.0.0.1/"),
        ("http://017.1/", "http://15.0.0.1/"),
        ("http://0/", "http://0.0.0.0/"),
        ("http://2130706433/", "http://127.0.0.1/"),
        ("http://256/", "http://0.0.1.0/"),
        ("http://4294967295/", "http://255.255.255.255/"),
        ("http://0xffffffff/", "http://255.255.255.255/"),
        ("http://192.168.257/", "http://192.168.1.1/"),
        ("http://192.168.257./", "http://192.168.1.1/"),
        ("https://0x.0x.0/", "https://0.0.0.0/"),
        ("https://00.00.00.00/", "https://0.0.0.0/"),
        ("https://000177.0.0.1/", "https://127.0.0.1/"),
        ("http://user:pass@256:8080/p?q#f", "http://user:pass@0.0.1.0:8080/p?q#f"),
        ("http://foo.0xg/", "http://foo.0xg/"),
        ("http://foo.0xgf/", "http://foo.0xgf/"),
        ("http://foo.bar/", "http://foo.bar/"),
        ("http://example.com./", "http://example.com./"),
        ("http://[::1]/", "http://[::1]/"),
        ("sc://foo.123/", "sc://foo.123/"),
        ("sc://256/", "sc://256/"),
    ],
)
def test_accepted(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


def test_parts() -> None:
    url = URL("http://user@0x7f.1:8080/")
    assert url.raw_host == url.host == "127.0.0.1"
    assert url.raw_authority == "user@127.0.0.1:8080"
    assert url.host_port_subcomponent == "127.0.0.1:8080"
    assert url == URL("http://user@127.0.0.1:8080/")


def test_build() -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL.build(scheme="http", host="foo.123")
    assert str(URL.build(scheme="http", host="256")) == "http://0.0.1.0"
    assert str(URL.build(scheme="sc", host="256")) == "sc://256"
    assert str(URL.build(scheme="sc", host="foo.123")) == "sc://foo.123"
    url = URL.build(scheme="http", host="foo.123", mode="rfc")
    assert str(url) == "http://foo.123"


def test_with_host() -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL("http://example.com/").with_host("foo.123")
    assert str(URL("sc://example.com/").with_host("foo.123")) == "sc://foo.123/"
    assert str(URL("http://example.com/").with_host("0x7f.1")) == "http://127.0.0.1/"
    url = URL("http://example.com/", mode="rfc").with_host("foo.123")
    assert str(url) == "http://foo.123/"


def test_build_authority() -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL.build(scheme="http", authority="user@foo.123:8080")
    url = URL.build(scheme="http", authority="foo.123", mode="rfc")
    assert str(url) == "http://foo.123"
    url = URL.build(scheme="http", authority="u@1.2.3:8080")
    assert str(url) == "http://u@1.2.0.3:8080"
    url = URL.build(scheme="http", authority="1.2.3", mode="rfc")
    assert str(url) == "http://1.2.3"


@pytest.mark.parametrize(
    "url", ["http://%30%78%63%30%2e%30%32%35%30.01/", "http://foo.%31/"]
)
def test_percent_encoded_host_left_alone(url: str) -> None:
    # yarl does not decode hosts, so it cannot tell what WHATWG would see.
    assert str(URL(url)) == url


def test_with_scheme() -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL("sc://foo.123/p").with_scheme("http")
    assert str(URL("sc://foo.123/p").with_scheme("tc")) == "tc://foo.123/p"
    url = URL("sc://u:p@1.2.3:81/p").with_scheme("http")
    assert str(url) == "http://u:p@1.2.0.3:81/p"
    assert str(URL("sc://1.2.3.4/p").with_scheme("http")) == "http://1.2.3.4/p"
    with pytest.raises(ValueError, match="ends in a number"):
        URL("sc://4294967296/p").with_scheme("http")
    url = URL("sc://foo.123/p", mode="rfc").with_scheme("http")
    assert str(url) == "http://foo.123/p"


@pytest.mark.parametrize("reference", ["//foo.123/path", "//foo.123/path?"])
def test_join(reference: str) -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL("http://example.com/").join(URL(reference))
    url = URL("http://example.com/", mode="rfc").join(URL(reference))
    assert url.host == "foo.123"


@pytest.mark.parametrize("reference", ["//256/path", "//256/path?"])
def test_join_ipv4(reference: str) -> None:
    url = URL("http://example.com/").join(URL(reference))
    assert url.raw_authority == "0.0.1.0"
    url = URL("http://example.com/", mode="rfc").join(URL(reference))
    assert url.raw_authority == "256"


def test_mode_change() -> None:
    url = URL("http://foo.123/", mode="rfc")
    with pytest.raises(ValueError, match="ends in a number"):
        URL(url, mode="whatwg")
    assert URL(URL("http://1.2.3/", mode="rfc"), mode="whatwg").host == "1.2.0.3"
    assert URL(URL("http://1.2.3/"), mode="rfc").host == "1.2.0.3"
    url = URL(URL("http://1.2.3.4/", mode="rfc"), mode="whatwg")
    assert str(url) == "http://1.2.3.4/"


@pytest.mark.parametrize("digits", ["1" * 5000, "0x" + "f" * 5000, "0" + "7" * 5000])
def test_huge_number(digits: str) -> None:
    # Longer than Python converts with int(); must not leak that error.
    with pytest.raises(ValueError, match="ends in a number"):
        URL(f"http://{digits}/")
    assert URL(f"http://{digits}/", mode="rfc").host == digits
    assert URL(f"sc://{digits}/").host == digits
