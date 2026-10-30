"""Conformance tests for RFC 5952, IPv6 Address Text Representation.

https://www.rfc-editor.org/rfc/rfc5952

RFC 3986 section 3.2.2 carries IPv6 addresses inside IP-literals, and
section 6.2.2.1 allows normalizing them; yarl emits the canonical text
form recommended by RFC 5952 section 4 in WHATWG mode, as the WHATWG URL
Standard does. RFC 3986 mode keeps the address as written, only
lowercased, since section 6.2.2 does not compress it.
"""

from collections.abc import Callable

import pytest

from yarl import URL, Mode

CANONICAL = [
    # Section 2.1: leading zeros.
    ("2001:db8:aaaa:bbbb:cccc:dddd:eeee:0001", "2001:db8:aaaa:bbbb:cccc:dddd:eeee:1"),
    ("2001:db8:aaaa:bbbb:cccc:dddd:eeee:001", "2001:db8:aaaa:bbbb:cccc:dddd:eeee:1"),
    ("2001:db8:aaaa:bbbb:cccc:dddd:eeee:01", "2001:db8:aaaa:bbbb:cccc:dddd:eeee:1"),
    ("2001:db8:aaaa:bbbb:cccc:dddd:eeee:1", "2001:db8:aaaa:bbbb:cccc:dddd:eeee:1"),
    # Section 2.2: zero compression.
    ("2001:db8:0:0:0::1", "2001:db8::1"),
    ("2001:db8:0:0::1", "2001:db8::1"),
    ("2001:db8:0::1", "2001:db8::1"),
    ("2001:db8::1", "2001:db8::1"),
    ("2001:db8::aaaa:0:0:1", "2001:db8::aaaa:0:0:1"),
    ("2001:db8:0:0:aaaa::1", "2001:db8::aaaa:0:0:1"),
    # Section 2.3: uppercase and lowercase.
    (
        "2001:db8:aaaa:bbbb:cccc:dddd:eeee:aaaa",
        "2001:db8:aaaa:bbbb:cccc:dddd:eeee:aaaa",
    ),
    (
        "2001:db8:aaaa:bbbb:cccc:dddd:eeee:AAAA",
        "2001:db8:aaaa:bbbb:cccc:dddd:eeee:aaaa",
    ),
    (
        "2001:db8:aaaa:bbbb:cccc:dddd:eeee:AaAa",
        "2001:db8:aaaa:bbbb:cccc:dddd:eeee:aaaa",
    ),
    # Section 4.1: handling leading zeros in a 16-bit field.
    ("2001:0db8::0001", "2001:db8::1"),
    # Section 4.2.1: shorten as much as possible.
    ("2001:db8:0:0:0:0:2:1", "2001:db8::2:1"),
    ("2001:db8::0:1", "2001:db8::1"),
    # Section 4.2.2: "::" must not shorten a single 16-bit 0 field.
    ("2001:db8:0:1:1:1:1:1", "2001:db8:0:1:1:1:1:1"),
    # Section 4.2.3: choice in placement of "::".
    ("2001:0:0:1:0:0:0:1", "2001:0:0:1::1"),
    ("2001:db8:0:0:1:0:0:1", "2001:db8::1:0:0:1"),
    # Section 4.3: lowercase.
    ("2001:DB8::ABCD", "2001:db8::abcd"),
    # Section 5: IPv4-mapped addresses keep the dotted quad.
    ("::ffff:192.0.2.1", "::ffff:192.0.2.1"),
    ("::ffff:c000:0201", "::ffff:192.0.2.1"),
    # RFC 4291 section 2.2 special forms.
    ("0:0:0:0:0:0:0:1", "::1"),
    ("0:0:0:0:0:0:0:0", "::"),
]


@pytest.mark.parametrize(("address", "canonical"), CANONICAL)
def test_canonical_text_form(address: str, canonical: str) -> None:
    url = URL(f"http://[{address}]/")
    assert url.raw_host == canonical
    assert url.host == canonical
    assert str(url) == f"http://[{canonical}]/"


@pytest.mark.parametrize(("address", "canonical"), CANONICAL)
def test_equivalent_forms_compare_equal(address: str, canonical: str) -> None:
    assert URL(f"http://[{address}]/") == URL(f"http://[{canonical}]/")


# Section 6: an address with a port is written as "[address]:port".
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://[2001:DB8::0001]:8080/", "http://[2001:db8::1]:8080/"),
        ("http://[2001:db8::1]:80/", "http://[2001:db8::1]/"),
    ],
)
def test_port_notation(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


def test_build_brackets_ipv6_host() -> None:
    url = URL.build(scheme="http", host="2001:DB8::0001", port=8080)
    assert str(url) == "http://[2001:db8::1]:8080"
    assert url.host_port_subcomponent == "[2001:db8::1]:8080"


@pytest.mark.parametrize(("address", "canonical"), CANONICAL)
def test_rfc_mode_keeps_address_as_written(address: str, canonical: str) -> None:
    url = URL(f"http://[{address}]/", mode="rfc")
    assert url.raw_host == address.lower()
    assert url.host == address.lower()
    assert str(url) == f"http://[{address.lower()}]/"
    assert str(URL(url, mode="whatwg")) == f"http://[{canonical}]/"


@pytest.mark.parametrize(
    "make",
    [
        lambda mode: URL("http://[1:0::]/", mode=mode),
        lambda mode: URL.build(scheme="http", host="1:0::", mode=mode),
        lambda mode: URL.build(scheme="http", authority="[1:0::]", mode=mode),
        lambda mode: URL("http://h/", mode=mode).with_host("1:0::"),
        lambda mode: URL("http://h/", mode=mode).join(URL("//[1:0::]/", mode=mode)),
        lambda mode: URL("sc://[1:0::]/", mode=mode).with_scheme("http"),
    ],
)
def test_written_address_by_mode(make: Callable[[Mode], URL]) -> None:
    assert make(Mode.RFC).raw_host == "1:0::"
    assert make(Mode.WHATWG).raw_host == "1::"


def test_rfc_mode_written_forms_differ() -> None:
    assert URL("http://[1:0::]/", mode="rfc") != URL("http://[1::]/", mode="rfc")


def test_rfc_mode_keeps_zone_id() -> None:
    url = URL("http://[FE80:0::1%25eth0]/", mode="rfc")
    assert str(url) == "http://[fe80:0::1%25eth0]/"
    assert str(URL(url, mode="whatwg")) == "http://[fe80::1%25eth0]/"
