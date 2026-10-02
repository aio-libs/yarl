"""Conformance tests for scheme-specific URI RFCs.

* RFC 9110 section 4.2, http and https URI schemes:
  https://www.rfc-editor.org/rfc/rfc9110#section-4.2
* RFC 6455 section 3, ws and wss URI schemes:
  https://www.rfc-editor.org/rfc/rfc6455#section-3
* RFC 8089, the file URI scheme:
  https://www.rfc-editor.org/rfc/rfc8089
* RFC 6068, the mailto URI scheme:
  https://www.rfc-editor.org/rfc/rfc6068
"""

import pytest

from yarl import URL


def diverges(reason: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(strict=True, reason=f"yarl: {reason}")


# RFC 9110 sections 4.2.1 and 4.2.2, RFC 6455 section 3: default ports.
@pytest.mark.parametrize(
    ("scheme", "port"),
    [("http", 80), ("https", 443), ("ws", 80), ("wss", 443)],
)
def test_default_port(scheme: str, port: int) -> None:
    url = URL(f"{scheme}://example.com:{port}/")
    assert url.port == port
    assert url.is_default_port()
    assert str(url) == f"{scheme}://example.com/"
    assert URL(f"{scheme}://example.com/").port == port


# RFC 9110 section 4.2.3: these three URIs are equivalent.
@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:80/~smith/home.html",
        "http://EXAMPLE.com/%7Esmith/home.html",
        "http://EXAMPLE.com:/%7esmith/home.html",
    ],
)
def test_http_normalization(url: str) -> None:
    assert str(URL(url)) == "http://example.com/~smith/home.html"


# RFC 9110 section 4.2.3: an empty path is equivalent to "/".
def test_http_empty_path() -> None:
    assert URL("http://example.com").path == "/"


# RFC 9110 section 4.2.1: a recipient must reject an http URI with an
# empty host identifier.
@pytest.mark.parametrize(
    "url",
    [
        "http://user@/",
        pytest.param(
            "http:///path",
            marks=diverges("WHATWG mode reads the path as the authority"),
        ),
        pytest.param(
            "https:///path",
            marks=diverges("WHATWG mode reads the path as the authority"),
        ),
        pytest.param(
            "http:/example.com/",
            marks=diverges("WHATWG mode reads the path as the authority"),
        ),
    ],
)
def test_http_empty_host_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        URL(url)


# RFC 8089 appendix B: forms of a local file URI.
@pytest.mark.parametrize(
    ("url", "host", "path"),
    [
        ("file:///path/to/file", None, "/path/to/file"),
        ("file:/path/to/file", None, "/path/to/file"),
        ("file://host.example.com/path/to/file", "host.example.com", "/path/to/file"),
    ],
)
def test_file_forms(url: str, host: str | None, path: str) -> None:
    u = URL(url)
    assert u.host == host
    assert u.path == path


# RFC 8089 section 2: "file:/path" and "file:///path" are equivalent.
def test_file_minimal_form_equivalent() -> None:
    assert URL("file:/path/to/file") == URL("file:///path/to/file")


# RFC 8089 appendix E.2: DOS and Windows drive letters. WHATWG mode writes
# "file:c:/path/to/file" as "file:///c:/path/to/file", as WHATWG does.
@pytest.mark.parametrize("url", ["file:///c:/path/to/file", "file:c:/path/to/file"])
def test_file_drive_letter_round_trips(url: str) -> None:
    assert str(URL(url, mode="rfc")) == url


# RFC 8089 appendix E.2.2: "|" in legacy drive letters is not allowed by
# RFC 3986. WHATWG mode reads it as ":", as WHATWG does.
def test_file_vertical_line_drive_letter() -> None:
    with pytest.raises(ValueError, match="do not allow '|'"):
        URL("file:///c|/path/to/file", mode="rfc")


# RFC 8089 appendix E.2.1 describes resolving against a drive letter as
# the root as a non-standard option; yarl follows RFC 3986 section 5.2 in
# RFC mode. WHATWG mode keeps the drive letter, as WHATWG does.
@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        (
            "file:///c:/path/to/file.txt",
            "/some/other/thing.bmp",
            "file:///some/other/thing.bmp",
        ),
        ("file:///c:/foo.txt", "../bar.txt", "file:///bar.txt"),
        ("file:///c:/path/to/file.txt", "other.txt", "file:///c:/path/to/other.txt"),
    ],
)
def test_file_drive_letter_join(base: str, reference: str, expected: str) -> None:
    joined = URL(base, mode="rfc").join(URL(reference, mode="rfc"))
    assert str(joined) == expected


# RFC 8089 appendix E.3.2: UNC paths with an empty authority.
def test_file_unc_path() -> None:
    url = URL("file:////host.example.com/path/to/file")
    assert url.host is None
    assert url.path == "//host.example.com/path/to/file"
    assert str(url) == "file:////host.example.com/path/to/file"


# RFC 6068 section 6: mailto examples.
@pytest.mark.parametrize(
    ("url", "path", "query"),
    [
        ("mailto:chris@example.com", "chris@example.com", {}),
        (
            "mailto:infobot@example.com?subject=current-issue",
            "infobot@example.com",
            {"subject": "current-issue"},
        ),
        (
            "mailto:list@example.org?In-Reply-To=%3C3469A91.D10AF4C@example.com%3E",
            "list@example.org",
            {"In-Reply-To": "<3469A91.D10AF4C@example.com>"},
        ),
        (
            "mailto:addr1@an.example,addr2@an.example",
            "addr1@an.example,addr2@an.example",
            {},
        ),
        (
            "mailto:?to=addr1@an.example,addr2@an.example",
            "",
            {"to": "addr1@an.example,addr2@an.example"},
        ),
        (
            "mailto:user@example.org?subject=%C3%A9t%C3%A9",
            "user@example.org",
            {"subject": "\u00e9t\u00e9"},
        ),
    ],
)
def test_mailto(url: str, path: str, query: dict[str, str]) -> None:
    u = URL(url)
    assert u.scheme == "mailto"
    assert u.host is None
    assert u.path == path
    assert dict(u.query) == query
    assert str(u) == url


# RFC 6068 section 6.2: a percent-encoded "@" in the local part is part
# of the address and must stay encoded.
@pytest.mark.parametrize(
    "url",
    [
        "mailto:%22%5C%5C%5C%22it's%5C%20ugly%5C%5C%5C%22%22@example.org",
        "mailto:%22not%40me%22@example.org",
    ],
)
def test_mailto_encoded_local_part(url: str) -> None:
    assert str(URL(url)) == url
