"""An authority that is only an empty port is kept in RFC 3986 mode.

RFC 3986 section 6.2.3 drops an empty port with its ":", so "sc://:/" is
"sc:///": the authority is present and empty. WHATWG mode rejects it.
"""

import pickle

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc://:/", "sc:///"),
        ("sc://:", "sc://"),
        ("sc://:?q", "sc://?q"),
        ("sc://:#f", "sc://#f"),
        ("sc://:/a/../b", "sc:///b"),
        ("sc://://a", "sc:////a"),
        ("//:/p", "///p"),
    ],
)
def test_parse(url: str, expected: str) -> None:
    rfc_url = URL(url, mode="rfc")
    assert str(rfc_url) == expected
    assert rfc_url.raw_authority == rfc_url.authority == ""
    assert rfc_url.raw_host is rfc_url.host is None
    assert rfc_url.explicit_port is None
    assert rfc_url == URL(expected, mode="rfc")
    assert hash(rfc_url) == hash(URL(expected, mode="rfc"))
    with pytest.raises(ValueError, match="host is required"):
        URL(url)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        # An empty port next to something else was kept already.
        ("sc://:12/", "sc://:12/"),
        ("sc://@:/", "sc://@/"),
        ("sc://u@:/", "sc://u@/"),
        ("sc://h:/", "sc://h/"),
    ],
)
def test_other_authority(url: str, expected: str) -> None:
    assert str(URL(url, mode="rfc")) == expected


def test_parts() -> None:
    url = URL("sc://:/a?q#f", mode="rfc")
    assert url.scheme == "sc"
    assert url.path == "/a"
    assert url.query_string == "q"
    assert url.fragment == "f"
    assert url.raw_user is None
    assert url.port is None
    assert not url.absolute


def test_pickle() -> None:
    url = URL("sc://:/a", mode="rfc")
    restored = pickle.loads(pickle.dumps(url))
    assert restored == url
    assert str(restored) == "sc:///a"


def test_http_host_required() -> None:
    # RFC 9110 section 4.2.1 still applies to http in RFC mode.
    with pytest.raises(ValueError, match="host is required"):
        URL("http://:/", mode="rfc")


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("//:/p", "sc:///p"),
        ("//:", "sc://"),
        ("//:?q", "sc://?q"),
    ],
)
def test_join_reference(ref: str, expected: str) -> None:
    # RFC 3986 section 5.2.2: the authority of the reference replaces the
    # one of the base, also when it is empty.
    base = URL("sc://x/y", mode="rfc")
    assert str(base.join(URL(ref, mode="rfc"))) == expected


def test_join_base() -> None:
    base = URL("sc://:/a/b", mode="rfc")
    assert str(base.join(URL("c", mode="rfc"))) == "sc:///a/c"
    assert str(base / "c") == "sc:///a/b/c"


@pytest.mark.parametrize(
    ("path", "query_string", "expected"),
    [
        ("", "", "sc://"),
        ("/a/../b", "", "sc:///b"),
        ("", "q", "sc://?q"),
    ],
)
def test_build(path: str, query_string: str, expected: str) -> None:
    url = URL.build(
        scheme="sc", authority=":", path=path, query_string=query_string, mode="rfc"
    )
    assert str(url) == expected
    assert url == URL(expected, mode="rfc")


def test_build_relative_path() -> None:
    with pytest.raises(ValueError, match="should start with a slash"):
        URL.build(scheme="sc", authority=":", path="a", mode="rfc")


def test_build_whatwg() -> None:
    with pytest.raises(ValueError, match="host is required"):
        URL.build(scheme="sc", authority=":")
