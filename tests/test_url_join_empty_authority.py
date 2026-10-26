"""join() of a reference with an empty authority against a base needing a host.

RFC 3986 section 5.2.2 takes the empty authority of a reference such as
"///a", and RFC 9110 section 4.2.1 rejects the resulting "http:///a", so RFC
3986 mode fails. The WHATWG URL Standard skips all the slashes after a
special scheme other than file and reads the host after them, so in WHATWG
mode "///a/b" against an http base is "http://a/b".
"""

import pickle

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        ("http://example.org/", "///test", "http://test"),
        ("http://example.org/", "///example.org/path", "http://example.org/path"),
        ("http://example.org/", "///example.org/../path", "http://example.org/path"),
        ("http://example.org/", "////a/b", "http://a/b"),
        ("http://example.org/", "///\\//\\//test", "http://test"),
        (
            "http://example.org/",
            "/\\/\\//example.org/../path",
            "http://example.org/path",
        ),
        ("http://example.org/", "///a?q#f", "http://a/?q#f"),
        ("http://example.org/", "///a?", "http://a/?"),
        ("http://example.org/", "///u:p@h:81/x", "http://u:p@h:81/x"),
        ("http://example.org/", "///[::1]/x", "http://[::1]/x"),
        ("http://example.org/", "/\\/\\/[::1]/x", "http://[::1]/x"),
        ("http://example.org/", "///%5Bu%5D@h/x", "http://%5Bu%5D@h/x"),
        ("http://example.org/", "///%41/x", "http://a/x"),
        ("http://example.org/", "///%C3%B1/x", "http://xn--ida/x"),
        ("http://example.org/", "///0x7f.1/", "http://127.0.0.1/"),
        ("https://example.org/a", "///b", "https://b"),
        ("ws://example.org/a", "///b:8080", "ws://b:8080"),
        ("ftp://example.org/a", "///b/c", "ftp://b/c"),
        # Other schemes keep the empty authority of the reference.
        ("sc://x/", "///a", "sc:///a"),
        ("file://h/", "///a", "file:///a"),
    ],
)
def test_join_whatwg(base: str, reference: str, expected: str) -> None:
    assert str(URL(base).join(URL(reference))) == expected


@pytest.mark.parametrize(
    "reference",
    [
        "//",
        "///",
        "//?q",
        "///#f",
        "///a%2Fb",
        # The port and the brackets of the host are read as written.
        "///h:%38%30/x",
        "/\\/\\/h:%38%30/x",
        "///%5B::1%5D/x",
        "///C|/x",
    ],
)
def test_join_whatwg_empty_host_rejected(reference: str) -> None:
    with pytest.raises(ValueError):
        URL("http://example.org/").join(URL(reference))


def test_join_whatwg_written_path_kept() -> None:
    # The path as written survives a new query and pickling.
    url = URL("///[::1]/x").with_query(a="1")
    base = URL("http://example.org/")
    assert str(base.join(url)) == "http://[::1]/x?a=1"
    assert str(base.join(pickle.loads(pickle.dumps(url)))) == "http://[::1]/x?a=1"


@pytest.mark.parametrize(
    "base", ["http://example.org/", "https://example.org/a", "ws://example.org/"]
)
@pytest.mark.parametrize("reference", ["///test", "///example.org/../path", "//"])
def test_join_rfc_empty_host_rejected(base: str, reference: str) -> None:
    with pytest.raises(ValueError, match="empty host"):
        URL(base, mode="rfc").join(URL(reference, mode="rfc"))


def test_join_rfc_other_scheme_keeps_empty_authority() -> None:
    base = URL("sc://x/", mode="rfc")
    assert str(base.join(URL("///a", mode="rfc"))) == "sc:///a"


@pytest.mark.parametrize("base", ["https://example.org/a", "sc://x/", "file:///a"])
@pytest.mark.parametrize("reference", ["http:", "http:?q", "http:/", "ws:"])
def test_join_whatwg_hostless_special_reference_rejected(
    base: str, reference: str
) -> None:
    # Only a base with the same scheme makes these references.
    with pytest.raises(ValueError, match="host is required"):
        URL(base).join(URL(reference))


@pytest.mark.parametrize(
    ("reference", "expected"),
    [("http:", "http://h/p?q"), ("http:?x", "http://h/p?x")],
)
def test_join_whatwg_hostless_special_reference_same_scheme(
    reference: str, expected: str
) -> None:
    assert str(URL("http://h/p?q").join(URL(reference))) == expected


def test_join_rfc_hostless_special_reference() -> None:
    base = URL("https://example.org/foo/bar", mode="rfc")
    assert str(base.join(URL("http:", mode="rfc"))) == "http:"
