"""An empty host is rejected for the special schemes that need one.

The WHATWG host parser fails on an empty host for every special scheme but
file, and RFC 9110 section 4.2.1 rejects an http URI with an empty host, so
"http://", "http:///" and "http://?q" are invalid in both modes. "http:" and
"http:?q" have no authority: they are references to a base, and are written
out without "//".
"""

import pickle
from collections.abc import Callable
from typing import Literal

import pytest

from yarl import URL


@pytest.mark.parametrize(
    "url",
    [
        "http://",
        "http:///",
        "http:////",
        "http://?",
        "http://#",
        "http://?q",
        "http:///?q",
        "http://#f",
        "HTTP://?",
        "https://",
        "ws://",
        "wss://?q",
        "ftp://#f",
    ],
)
@pytest.mark.parametrize("mode", ["whatwg", "rfc"])
def test_rejected(url: str, mode: Literal["whatwg", "rfc"]) -> None:
    with pytest.raises(ValueError, match="host is required"):
        URL(url, mode=mode)


def test_path_after_empty_authority() -> None:
    # WHATWG mode skips the slashes and reads "p" as the host.
    assert str(URL("http:///p")) == "http://p"
    with pytest.raises(ValueError, match="host is required"):
        URL("http:///p", mode="rfc")


@pytest.mark.parametrize("url", ["file://", "sc://", "sc://?q"])
def test_other_schemes(url: str) -> None:
    # A file URL and a non-special URL may have an empty host.
    assert URL(url).raw_host is None


@pytest.mark.parametrize("url", ["http:", "http:/", "http:?q=1", "http:#f", "ws:?"])
def test_reference_without_authority(url: str) -> None:
    whatwg_url = URL(url)
    assert str(whatwg_url) == url
    assert whatwg_url.raw_host is None
    assert whatwg_url.raw_authority == ""
    assert whatwg_url.human_repr() == url
    assert URL(str(whatwg_url)) == whatwg_url
    assert pickle.loads(pickle.dumps(whatwg_url)) == whatwg_url
    rfc_url = URL(url, mode="rfc")
    assert str(rfc_url) == url
    assert whatwg_url == rfc_url
    assert hash(whatwg_url) == hash(rfc_url)


def test_reference_not_equal_with_root_path() -> None:
    assert URL("http:") != URL("http:/")


@pytest.mark.parametrize(
    ("make", "expected"),
    [
        (lambda: URL.build(scheme="http"), "http:"),
        (lambda: URL.build(scheme="https", query_string="q"), "https:?q"),
        (lambda: URL("http:").with_query("a=1"), "http:?a=1"),
        (lambda: URL("http:").with_fragment("f"), "http:#f"),
        (lambda: URL("http:?q").parent, "http:"),
    ],
)
def test_derived(make: Callable[[], URL], expected: str) -> None:
    assert str(make()) == expected


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("http:", "http://h/a?x"),
        ("http:?q", "http://h/a?q"),
        ("http:#f", "http://h/a?x#f"),
    ],
)
def test_join(reference: str, expected: str) -> None:
    # Against a base with the same scheme it is a relative reference.
    assert str(URL("http://h/a?x").join(URL(reference))) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [("http:", "http:"), ("sc://", "sc://"), ("file://", "file:///")],
)
def test_mode_change(url: str, expected: str) -> None:
    assert str(URL(URL(url, mode="rfc"))) == expected
