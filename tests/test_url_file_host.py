"""WHATWG mode drops "localhost" from a file URL and rejects userinfo and ports."""

import pickle
from typing import TypedDict

import pytest

from yarl import URL

FILE_AUTHORITY = "a file URL cannot have userinfo or a port"


class BuildArgs(TypedDict, total=False):
    authority: str
    user: str
    password: str
    host: str
    port: int
    path: str


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        ("file://localhost", "file:///", "file://localhost"),
        ("file://localhost/", "file:///", "file://localhost/"),
        ("file://localhost/test", "file:///test", "file://localhost/test"),
        ("file://LOCALHOST/test", "file:///test", "file://localhost/test"),
        ("file://loc%61lhost/test", "file:///test", "file://loc%61lhost/test"),
        ("file://localhost////foo", "file://////foo", "file://localhost////foo"),
        (
            "file://localhost//a//../..//foo",
            "file://///foo",
            "file://localhost///foo",
        ),
        ("file://localhost/a?q#f", "file:///a?q#f", "file://localhost/a?q#f"),
        # Only "localhost" itself is dropped.
        ("file://localhost./x", "file://localhost./x", "file://localhost./x"),
        ("file://example/x", "file://example/x", "file://example/x"),
        ("file://[::1]/x", "file://[::1]/x", "file://[::1]/x"),
        # Other schemes keep it.
        ("http://localhost/x", "http://localhost/x", "http://localhost/x"),
        ("sc://localhost/x", "sc://localhost/x", "sc://localhost/x"),
    ],
)
def test_parse(url: str, whatwg: str, rfc: str) -> None:
    whatwg_url = URL(url)
    assert str(whatwg_url) == whatwg
    assert URL(whatwg) == whatwg_url
    assert hash(URL(whatwg)) == hash(whatwg_url)
    assert str(URL(url, mode="rfc")) == rfc


def test_parse_localhost_parts() -> None:
    url = URL("file://localhost")
    assert url.raw_host is None
    assert url.host is None
    assert url.raw_authority == ""
    assert url.raw_path == "/"
    assert url == URL("file:///")
    # The empty authority is kept in RFC mode.
    assert str(URL(url, mode="rfc")) == "file:///"


def test_parse_backslashes() -> None:
    assert str(URL("file:\\\\localhost//")) == "file:////"
    with pytest.raises(ValueError, match="does not allow"):
        URL("file:\\\\localhost//", mode="rfc")


@pytest.mark.parametrize(
    "url",
    [
        "file://example:1/",
        "file://example:/",
        "file://localhost:1/",
        "file://[::1]:1/",
        "file://user@example/",
        "file://user:pass@example/",
        "file://@example/",
        "file://:@example/",
    ],
)
def test_parse_rejected(url: str) -> None:
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        URL(url)
    URL(url, mode="rfc")


def test_parse_drive_letter_is_not_a_port() -> None:
    # The Windows drive letter is left as yarl parsed it before.
    assert str(URL("file://C:/x")) == "file://c/x"


def test_parse_encoded_is_kept() -> None:
    url = URL("file://localhost:1/x", encoded=True)
    assert str(url) == "file://localhost:1/x"


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("//localhost//pig", "file:////pig"),
        ("\\/localhost//pig", "file:////pig"),
        ("//LOCALHOST/x?q", "file:///x?q"),
        ("//localhost", "file:///"),
        ("//localhost?", "file:///?"),
        ("//example/x", "file://example/x"),
    ],
)
def test_join(reference: str, expected: str) -> None:
    joined = URL("file://lion/").join(URL(reference))
    assert str(joined) == expected
    assert joined == URL(expected)


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("//localhost//pig", "file://localhost//pig"),
        ("//example:1/", "file://example:1/"),
    ],
)
def test_join_rfc(reference: str, expected: str) -> None:
    base = URL("file://lion/", mode="rfc")
    assert str(base.join(URL(reference, mode="rfc"))) == expected


@pytest.mark.parametrize("reference", ["//example:1/", "//u@example/", "//u@h?"])
def test_join_rejected(reference: str) -> None:
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        URL("file://lion/").join(URL(reference))


def test_join_rfc_reference() -> None:
    reference = URL("file://localhost/y", mode="rfc")
    assert str(URL("file:///x").join(reference)) == "file:///y"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file://localhost/x", "file:///x"),
        ("file://localhost", "file:///"),
        ("file://example/x", "file://example/x"),
    ],
)
def test_mode_change(url: str, expected: str) -> None:
    assert str(URL(URL(url, mode="rfc"), mode="whatwg")) == expected


@pytest.mark.parametrize("url", ["file://example:1/", "file://user@example/"])
def test_mode_change_rejected(url: str) -> None:
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        URL(URL(url, mode="rfc"), mode="whatwg")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost/x", "file:///x"),
        ("sc://localhost", "file:///"),
        ("http://LOC%61LHOST/", "file:///"),
        ("sc://example/x", "file://example/x"),
    ],
)
def test_with_scheme(url: str, expected: str) -> None:
    assert str(URL(url).with_scheme("file")) == expected
    assert URL(url, mode="rfc").with_scheme("file").raw_host


@pytest.mark.parametrize("url", ["http://example:8080/", "sc://user@example/"])
def test_with_scheme_rejected(url: str) -> None:
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        URL(url).with_scheme("file")
    assert URL(url, mode="rfc").with_scheme("file").raw_host == "example"


@pytest.mark.parametrize(
    ("kwargs", "whatwg", "rfc"),
    [
        ({"host": "localhost"}, "file:///", "file://localhost"),
        ({"host": "LOCALHOST", "path": "/a/../b"}, "file:///b", "file://localhost/b"),
        ({"host": "loc%61lhost"}, "file:///", "file://loc%61lhost"),
        ({"authority": "localhost"}, "file:///", "file://localhost"),
        ({"host": "example", "path": "/x"}, "file://example/x", "file://example/x"),
    ],
)
def test_build(kwargs: BuildArgs, whatwg: str, rfc: str) -> None:
    built = URL.build(scheme="file", **kwargs)
    assert str(built) == whatwg
    assert built == URL(whatwg)
    assert str(URL.build(scheme="file", mode="rfc", **kwargs)) == rfc


def test_build_localhost_needs_absolute_path() -> None:
    with pytest.raises(ValueError, match="should start with a slash"):
        URL.build(scheme="file", host="localhost", path="x")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"host": "example", "port": 1},
        {"host": "example", "user": "u"},
        {"host": "example", "password": "p"},
        {"authority": "example:1"},
        {"authority": "example:"},
        {"authority": "u@example"},
    ],
)
def test_build_rejected(kwargs: BuildArgs) -> None:
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        URL.build(scheme="file", **kwargs)
    URL.build(scheme="file", mode="rfc", **kwargs)


def test_build_encoded_is_kept() -> None:
    url = URL.build(scheme="file", host="localhost", port=1, encoded=True)
    assert str(url) == "file://localhost:1"


@pytest.mark.parametrize(
    ("url", "host", "expected"),
    [
        ("file://example/x", "localhost", "file:///x"),
        ("file://example/x", "LOC%61LHOST", "file:///x"),
        ("file://example", "localhost", "file:///"),
        ("file://example/x", "other", "file://other/x"),
    ],
)
def test_with_host(url: str, host: str, expected: str) -> None:
    replaced = URL(url).with_host(host)
    assert str(replaced) == expected
    assert replaced == URL(expected)
    assert URL(url, mode="rfc").with_host(host).raw_host


def test_with_port() -> None:
    url = URL("file://example/x")
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        url.with_port(1)
    assert url.with_port(None) == url
    assert str(URL(url, mode="rfc").with_port(1)) == "file://example:1/x"


def test_with_user() -> None:
    url = URL("file://example/x")
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        url.with_user("u")
    assert url.with_user(None) == url
    assert str(URL(url, mode="rfc").with_user("u")) == "file://u@example/x"


def test_with_password() -> None:
    url = URL("file://example/x")
    with pytest.raises(ValueError, match=FILE_AUTHORITY):
        url.with_password("p")
    assert url.with_password(None) == url
    assert str(URL(url, mode="rfc").with_password("p")) == "file://:p@example/x"


def test_path_building() -> None:
    url = URL("file://localhost/a/")
    assert str(url / "b") == "file:///a/b"
    assert str(url.joinpath("b", "c")) == "file:///a/b/c"
    assert str(url.with_path("/c")) == "file:///c"
    assert str(url.join(URL("../d"))) == "file:///d"
    assert str(URL("file://localhost/a/b").parent) == "file:///a"


def test_pickle() -> None:
    url = URL("file://localhost/x")
    assert pickle.loads(pickle.dumps(url)) == url


@pytest.mark.parametrize("base", ["file://localhost/a/", "file:///a/", "file:/a/"])
def test_empty_host_removes_dot_segments(base: str) -> None:
    # A file URL has an authority in WHATWG mode, also an empty one, so its
    # path loses dot segments as one with a host does.
    url = URL(base)
    assert str(url.with_path("/a/../b")) == "file:///b"
    assert str(url.with_path("a/../b")) == "file:///b"
    assert str(url / "../b") == "file:///b"
    assert str(url.joinpath("x/../y")) == "file:///a/y"
    assert str(URL(f"{base}x/../y")) == "file:///a/y"
    assert str(url.join(URL("x/../y"))) == "file:///a/y"


def test_empty_host_removes_dot_segments_build() -> None:
    assert str(URL.build(scheme="file", path="/a/../b")) == "file:///b"
    assert str(URL.build(scheme="file", path="/a/b")) == "file:///a/b"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file:///a/../b", "file:///b"),
        ("file:/a/../b", "file:/b"),
    ],
)
def test_empty_host_dot_segments_rfc(url: str, expected: str) -> None:
    rfc_url = URL(url, mode="rfc")
    assert str(rfc_url) == expected
    assert str(rfc_url.with_path("/a/../b")) == expected
