"""IPv6 zone identifiers in URIs.

RFC 6874 added the ``[fe80::1%25eth0]`` syntax to RFC 3986 IP-literals.
RFC 9844 (August 2025) obsoletes RFC 6874 and removes that syntax,
leaving zone identifiers as a user interface concern only; the WHATWG
URL Standard never supported them.  yarl keeps accepting the RFC 6874
form as legacy behaviour, covered in detail by the ``test_ipv6_zone_*``
tests in ``tests/test_url.py`` and ``tests/test_url_build.py``, which
also reject the empty zone identifier (RFC 9844 section 6.3).

https://www.rfc-editor.org/rfc/rfc6874
https://www.rfc-editor.org/rfc/rfc9844
"""

import pytest

from yarl import URL


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


# RFC 6874 section 3 describes a bare "%" as something user interfaces
# may accept; it is not valid URI syntax and yarl keeps it verbatim.
def test_bare_percent_zone_id_accepted() -> None:
    assert str(URL("http://[fe80::1%eth0]/")) == "http://[fe80::1%eth0]/"
