"""IPv6 zone identifiers in URIs.

RFC 6874 added the ``[fe80::1%25eth0]`` syntax to RFC 3986 IP-literals.
RFC 9844 (August 2025) obsoletes RFC 6874 and removes that syntax,
leaving zone identifiers as a user interface concern only; the WHATWG
URL Standard never supported them.  yarl keeps accepting the RFC 6874
form as legacy behaviour in both modes, and only that form, covered in
detail by the ``test_ipv6_zone_*`` tests in ``tests/test_url.py`` and
``tests/test_url_build.py``.

https://www.rfc-editor.org/rfc/rfc6874
https://www.rfc-editor.org/rfc/rfc9844
"""

import pytest

from yarl import URL, Mode


# RFC 6874 section 2: the "%" delimiter is percent-encoded as "%25".
@pytest.mark.parametrize(
    ("url", "raw_host", "host"),
    [
        ("http://[fe80::a%25en1]/", "fe80::a%25en1", "fe80::a%en1"),
        ("http://[fe80::1%254]:8080/", "fe80::1%254", "fe80::1%4"),
    ],
)
def test_rfc6874_zone_id_legacy(url: str, raw_host: str, host: str) -> None:
    u = URL(url)
    assert u.raw_host == raw_host
    assert u.host == host
    assert str(u) == url


# A bare "%", the user interface form of RFC 6874 section 3 and RFC 9844,
# is not URI syntax, and neither is a zone identifier that does not
# start with "%25", such as "%31" (an encoded "1"), which both RFC 3986 and
# WHATWG reject.
@pytest.mark.parametrize(
    "url",
    [
        "http://[fe80::1%eth0]/",
        "http://[fe80::a%ee1]/",
        "http://[fe80::1%]/",
        "http://[::%31]/",
        "http://[fe80::1%25e%2]/",
        "http://[fe80::1%25e th]/",
    ],
)
@pytest.mark.parametrize("mode", [Mode.WHATWG, Mode.RFC])
@pytest.mark.parametrize("encoded", [False, True])
def test_non_rfc6874_zone_id_rejected(url: str, mode: Mode, encoded: bool) -> None:
    with pytest.raises(ValueError, match="Invalid"):
        URL(url, mode=mode, encoded=encoded)


def test_non_rfc6874_zone_id_rejected_in_authority() -> None:
    with pytest.raises(ValueError, match="Invalid IPv6 zone identifier"):
        URL.build(scheme="http", authority="[fe80::1%eth0]")
    url = URL.build(scheme="http", authority="[fe80::1%25eth0]")
    assert url.host == "fe80::1%eth0"


@pytest.mark.parametrize("mode", [Mode.WHATWG, Mode.RFC])
def test_rfc6874_zone_id_mode_conversion(mode: Mode) -> None:
    url = URL("http://[fe80::1%25eth0]/", mode=mode)
    other = URL(url, mode=Mode.RFC if mode is Mode.WHATWG else Mode.WHATWG)
    assert str(other) == "http://[fe80::1%25eth0]/"
    assert other.host == "fe80::1%eth0"
