"""WHATWG mode gives a file URL an authority and a path, "/" at least."""

import pickle
from typing import TypedDict

import pytest

from yarl import URL


class BuildArgs(TypedDict, total=False):
    authority: str
    host: str
    query_string: str
    fragment: str


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        ("file:", "file:///", "file:"),
        ("file:?q=v", "file:///?q=v", "file:?q=v"),
        ("file:#frag", "file:///#frag", "file:#frag"),
        ("file:?", "file:///?", "file:?"),
        ("file://", "file:///", "file://"),
        ("file://test", "file://test/", "file://test"),
        ("file://test?q", "file://test/?q", "file://test/?q"),
        ("FILE:", "file:///", "file:"),
        # Other schemes keep the empty path.
        ("http://h", "http://h", "http://h"),
        ("sc:", "sc:", "sc:"),
        ("sc://h", "sc://h", "sc://h"),
    ],
)
def test_parse(url: str, whatwg: str, rfc: str) -> None:
    whatwg_url = URL(url)
    assert str(whatwg_url) == whatwg
    assert URL(whatwg) == whatwg_url
    assert hash(URL(whatwg)) == hash(whatwg_url)
    assert str(URL(url, mode="rfc")) == rfc


def test_parse_parts() -> None:
    url = URL("file:?q")
    assert url.raw_path == "/"
    assert url.path == "/"
    assert url.raw_authority == ""
    assert url.query_string == "q"
    # The empty authority goes along to RFC mode.
    assert str(URL(url, mode="rfc")) == "file:///?q"


def test_parse_encoded_is_kept() -> None:
    assert str(URL("file:", encoded=True)) == "file://"
    assert str(URL("file://test", encoded=True)) == "file://test"


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("file:", "file://host/dir/page?bq"),
        ("file:?q", "file://host/dir/page?q"),
        ("file:?", "file://host/dir/page?"),
        ("file:#f", "file://host/dir/page?bq#f"),
        ("file:?q#f", "file://host/dir/page?q#f"),
        ("file://test", "file://test/"),
        ("//test", "file://test/"),
        ("//test?q", "file://test/?q"),
        ("file://", "file:///"),
        ("//", "file:///"),
        ("file:///", "file:///"),
        # Unchanged references, against a file base with a host.
        ("", "file://host/dir/page?bq"),
        ("?q", "file://host/dir/page?q"),
        ("#f", "file://host/dir/page?bq#f"),
        ("a", "file://host/dir/a"),
        ("file:a", "file://host/dir/a"),
        ("file:./a", "file://host/dir/a"),
        ("file:.", "file://host/dir/"),
        ("file:../..", "file://host/"),
        ("a/../..", "file://host/"),
        ("file:a/..", "file://host/dir/"),
        ("/x", "file://host/x"),
        ("file:/x", "file://host/x"),
    ],
)
def test_join(reference: str, expected: str) -> None:
    joined = URL("file://host/dir/page?bq#bf").join(URL(reference))
    assert str(joined) == expected
    assert URL(expected) == joined


@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        ("file:", "a", "file:///a"),
        ("file:", "file:?q", "file:///?q"),
        ("file:///C:/a?bq", "file:", "file:///C:/a?bq"),
        ("file:///C:/a?bq", "file:#f", "file:///C:/a?bq#f"),
        ("file:///tmp/mock/path", "file://test", "file://test/"),
        ("file:///tmp/mock/path", "//", "file:///"),
        ("file://ape/", "file://", "file:///"),
        # Against another scheme "file:" stands alone.
        ("http://h/a", "file:?q", "file:///?q"),
    ],
)
def test_join_other_base(base: str, reference: str, expected: str) -> None:
    joined = URL(base).join(URL(reference))
    assert str(joined) == expected
    assert URL(expected) == joined


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("file:", "file:"),
        ("file:?q", "file:?q"),
        ("file://test", "file://test"),
        ("//test", "file://test"),
        ("?q", "file://host/dir/page?q"),
    ],
)
def test_join_rfc(reference: str, expected: str) -> None:
    base = URL("file://host/dir/page", mode="rfc")
    assert str(base.join(URL(reference, mode="rfc"))) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file:", "file:///"),
        ("file:?q", "file:///?q"),
        ("file://test", "file://test/"),
        ("file://localhost", "file:///"),
    ],
)
def test_mode_change(url: str, expected: str) -> None:
    moved = URL(URL(url, mode="rfc"), mode="whatwg")
    assert str(moved) == expected
    assert moved == URL(expected)


@pytest.mark.parametrize(
    ("url", "joined"),
    [
        ("file:", "file://host/dir/page?bq"),
        ("file:?q", "file://host/dir/page?q"),
        ("file:#f", "file://host/dir/page?bq#f"),
        ("file:///?q", "file:///?q"),
        ("file://localhost?q", "file:///?q"),
        ("file://test", "file://test/"),
    ],
)
def test_mode_change_join(url: str, joined: str) -> None:
    moved = URL(URL(url, mode="rfc"), mode="whatwg")
    base = URL("file://host/dir/page?bq#bf")
    assert str(base.join(moved)) == joined
    assert base.join(moved) == base.join(URL(url))
    assert pickle.loads(pickle.dumps(moved)) == moved
    assert str(base.join(pickle.loads(pickle.dumps(moved)))) == joined


def test_mode_change_keeps_shared_url() -> None:
    # The URL a mode change makes for "file:?q" is its own, the parsed
    # "file:///?q" is still no reference to the path of a base.
    URL(URL("file:?q", mode="rfc"))
    joined = URL("file://host/dir/page").join(URL("file:///?q"))
    assert str(joined) == "file:///?q"


@pytest.mark.parametrize(
    ("reference", "expected"),
    [("a", "file:///a"), ("/a", "file:///a"), ("?q", "file://?q")],
)
def test_join_encoded_base(reference: str, expected: str) -> None:
    # encoded=True keeps the empty path of the base.
    base = URL("file:", encoded=True)
    assert str(base.join(URL(reference))) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://h", "file://h/"),
        ("http://h?q", "file://h/?q"),
        ("sc://h", "file://h/"),
        ("http://localhost", "file:///"),
    ],
)
def test_with_scheme(url: str, expected: str) -> None:
    moved = URL(url).with_scheme("file")
    assert str(moved) == expected
    assert moved == URL(expected)


@pytest.mark.parametrize(
    ("url", "expected", "joined"),
    [
        ("sc:", "file:///", "file://host/dir/page?bq"),
        ("sc:?q", "file:///?q", "file://host/dir/page?q"),
        ("sc:#f", "file:///#f", "file://host/dir/page?bq#f"),
        ("sc:/?q", "file:///?q", "file://host/?q"),
        ("sc:///", "file:///", "file:///"),
    ],
)
def test_with_scheme_without_authority(url: str, expected: str, joined: str) -> None:
    moved = URL(url).with_scheme("file")
    assert str(moved) == expected
    assert moved == URL(expected)
    # As a reference it means what its string does.
    base = URL("file://host/dir/page?bq#bf")
    assert str(base.join(moved)) == joined
    assert base.join(URL(expected[:5] + url[3:])) == base.join(moved)


def test_with_scheme_rfc() -> None:
    url = URL("sc://h", mode="rfc").with_scheme("file")
    assert str(url) == "file://h"


@pytest.mark.parametrize(
    ("kwargs", "whatwg", "rfc"),
    [
        ({}, "file:///", "file:"),
        ({"query_string": "q"}, "file:///?q", "file:?q"),
        ({"fragment": "f"}, "file:///#f", "file:#f"),
        ({"host": "test"}, "file://test/", "file://test"),
        ({"authority": "test"}, "file://test/", "file://test"),
        ({"host": "localhost"}, "file:///", "file://localhost"),
        ({"authority": "C:"}, "file:///C:", "file://c"),
    ],
)
def test_build(kwargs: BuildArgs, whatwg: str, rfc: str) -> None:
    url = URL.build(scheme="file", **kwargs)
    assert str(url) == whatwg
    assert URL(whatwg) == url
    assert str(URL.build(scheme="file", mode="rfc", **kwargs)) == rfc


def test_build_encoded_is_kept() -> None:
    assert str(URL.build(scheme="file", encoded=True)) == "file://"


@pytest.mark.parametrize(
    ("url", "path", "whatwg", "rfc"),
    [
        ("file:///x", "", "file:///", "file://"),
        ("file:///x", "a/..", "file:///", "file:///"),
        ("file:///x", "/a/..", "file:///", "file:///"),
        ("file://h/x", "", "file://h/", "file://h"),
        ("file://h/x", "a/..", "file://h/", "file://h"),
    ],
)
def test_with_path(url: str, path: str, whatwg: str, rfc: str) -> None:
    replaced = URL(url).with_path(path)
    assert str(replaced) == whatwg
    assert URL(whatwg) == replaced
    assert str(URL(url, mode="rfc").with_path(path)) == rfc


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file:///a", "file:///"),
        ("file:///C:", "file:///"),
        ("file:///", "file:///"),
        ("file://h/a", "file://h/"),
    ],
)
def test_parent(url: str, expected: str) -> None:
    parent = URL(url).parent
    assert str(parent) == expected
    assert URL(expected) == parent


def test_parent_rfc() -> None:
    assert str(URL("file:///a", mode="rfc").parent) == "file://"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file:a/..", "file:///"),
        ("file:a/../", "file:///"),
        ("file:./", "file:///"),
    ],
)
def test_rootless_dot_segments(url: str, expected: str) -> None:
    assert str(URL(url)) == expected
    assert URL(expected) == URL(url)


def test_path_building() -> None:
    assert str(URL("file:") / "a") == "file:///a"
    assert str(URL("file://h").joinpath("a")) == "file://h/a"
    assert str(URL("file://h") / "") == "file://h/"


@pytest.mark.parametrize("url", ["file:", "file://h", "file:?q"])
def test_with_query_and_fragment(url: str) -> None:
    whatwg = URL(url)
    assert URL(str(whatwg.with_query("a=b"))) == whatwg.with_query("a=b")
    assert URL(str(whatwg.with_fragment("f"))) == whatwg.with_fragment("f")


def test_with_host() -> None:
    url = URL("file://h").with_host("example")
    assert str(url) == "file://example/"
    assert str(URL("file://h").with_host("localhost")) == "file:///"


def test_pickle() -> None:
    url = URL("file:?q")
    assert pickle.loads(pickle.dumps(url)) == url
    assert str(pickle.loads(pickle.dumps(url))) == "file:///?q"
