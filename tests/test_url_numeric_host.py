"""Hosts of special schemes that end in a number cannot have a name label.

The WHATWG URL Standard parses such a host, like "foo.123", as an IPv4
address and rejects it because "foo" is not a number. yarl follows that
decision in WHATWG mode; hosts made only of numbers keep being accepted as
written, and RFC 3986 mode accepts all of them as a reg-name.
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
    ],
)
def test_rejected(url: str) -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL(url)


@pytest.mark.parametrize("url", ["http://foo.123/", "https://foo.0x/", "ws://foo.09/"])
def test_accepted_in_rfc_mode(url: str) -> None:
    # RFC 3986 treats these hosts as a plain reg-name.
    assert str(URL(url, mode="rfc")) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://1.2.3.4/",
        "http://1.2.3.4./",
        "http://1.2.3/",
        "http://0x7f.1/",
        "http://0x.1/",
        "http://017.1/",
        "http://2130706433/",
        "http://1.2.3.4.5/",
        "http://256.1.1.1/",
        "http://12345678901234567890123456789012345678901234567890/",
        "http://foo.0xg/",
        "http://foo.bar/",
        "http://example.com./",
        "http://[::1]/",
        "sc://foo.123/",
    ],
)
def test_accepted(url: str) -> None:
    assert str(URL(url)) == url


def test_build() -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL.build(scheme="http", host="foo.123")
    assert str(URL.build(scheme="sc", host="foo.123")) == "sc://foo.123"
    url = URL.build(scheme="http", host="foo.123", mode="rfc")
    assert str(url) == "http://foo.123"


def test_with_host() -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL("http://example.com/").with_host("foo.123")
    assert str(URL("sc://example.com/").with_host("foo.123")) == "sc://foo.123/"
    url = URL("http://example.com/", mode="rfc").with_host("foo.123")
    assert str(url) == "http://foo.123/"


def test_build_authority() -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL.build(scheme="http", authority="user@foo.123:8080")
    url = URL.build(scheme="http", authority="foo.123", mode="rfc")
    assert str(url) == "http://foo.123"
    assert str(URL.build(scheme="http", authority="1.2.3")) == "http://1.2.3"


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
    assert str(URL("sc://1.2.3/p").with_scheme("http")) == "http://1.2.3/p"
    url = URL("sc://foo.123/p", mode="rfc").with_scheme("http")
    assert str(url) == "http://foo.123/p"


@pytest.mark.parametrize("reference", ["//foo.123/path", "//foo.123/path?"])
def test_join(reference: str) -> None:
    with pytest.raises(ValueError, match="ends in a number"):
        URL("http://example.com/").join(URL(reference))
    url = URL("http://example.com/", mode="rfc").join(URL(reference))
    assert url.host == "foo.123"


def test_mode_change() -> None:
    url = URL("http://foo.123/", mode="rfc")
    with pytest.raises(ValueError, match="ends in a number"):
        URL(url, mode="whatwg")
    assert URL(URL("http://1.2.3/", mode="rfc"), mode="whatwg").host == "1.2.3"
