"""WHATWG mode keeps Windows drive letters in file URLs, as WHATWG does.

https://url.spec.whatwg.org/#windows-drive-letter
"""

import pickle
from typing import TypedDict

import pytest

from yarl import URL


class BuildArgs(TypedDict, total=False):
    authority: str
    host: str
    path: str


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        # "|" is read as ":" in the first segment only.
        ("file:/C|/m/", "file:///C:/m/", None),
        ("file:/C|/", "file:///C:/", None),
        ("file:///C|/m", "file:///C:/m", None),
        ("file:///w|", "file:///w:", None),
        ("file://host/C|/x", "file://host/C:/x", None),
        ("file:/C||/m/", "file:///C%7C%7C/m/", None),
        ("file:///C|a", "file:///C%7Ca", None),
        ("file:///a/C|", "file:///a/C%7C", None),
        ("file:////C|/", "file:////C%7C/", None),
        ("file:///C%7C/", "file:///C%7C/", "file:///C%7C/"),
        ("http://h/C|/", "http://h/C%7C/", None),
        # A drive letter in the authority is the start of the path.
        ("file://C:/x", "file:///C:/x", "file://c/x"),
        ("file://C|/", "file:///C:/", None),
        ("file://c|", "file:///c:", None),
        ("file://C:?q#f", "file:///C:?q#f", "file://c/?q#f"),
        # ".." does not remove it.
        ("file:///C:/..", "file:///C:/", "file:///"),
        ("file:///C:/a/../..", "file:///C:/", "file:///"),
        ("file://h/C:/a/./../../b", "file://h/C:/b", "file://h/b"),
        ("file://C:/x/../..", "file:///C:/", "file://c/"),
        ("file:///a/../C:/..", "file:///C:/", "file:///"),
        ("http://h/C:/..", "http://h/", "http://h/"),
    ],
)
def test_parse(url: str, whatwg: str, rfc: str | None) -> None:
    parsed = URL(url)
    assert str(parsed) == whatwg
    assert URL(whatwg) == parsed
    if rfc is None:
        with pytest.raises(ValueError, match="do not allow '|'"):
            URL(url, mode="rfc")
    else:
        assert str(URL(url, mode="rfc")) == rfc


def test_parse_rootless() -> None:
    # The path stays rootless, as for "file:a/b".
    assert str(URL("file:C|/m/")) == "file:///C:/m/"
    assert URL("file:C|/m/").raw_path == "C:/m/"
    assert str(URL("file:C||/m/")) == "file:///C%7C%7C/m/"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file:C|/a/../..", "file:///C:/"),
        ("file:C:/a/./b", "file:///C:/a/b"),
        ("file:a/../b", "file:///b"),
        ("file:.", "file:///"),
        ("file:.//p", "file:////p"),
    ],
)
def test_parse_rootless_dot_segments(url: str, expected: str) -> None:
    # The path of a file URL is absolute in WHATWG mode, so dot segments are
    # removed as they are from "file:///...", and the URL survives str().
    parsed = URL(url)
    assert str(parsed) == expected
    assert URL(expected) == parsed
    assert URL(str(parsed)) == parsed


def test_parse_parts() -> None:
    url = URL("file://C|/a")
    assert url.raw_host is None
    assert url.raw_authority == ""
    assert url.path == "/C:/a"
    assert url.parts == ("/", "C:", "a")


@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        # A drive letter replaces the path of the base, keeping its host.
        ("file:///tmp/mock/path", "C|/foo/bar", "file:///C:/foo/bar"),
        ("file:///tmp/mock/path", "/C|\\foo\\bar", "file:///C:/foo/bar"),
        ("file:///tmp/mock/path", "file:c:\\foo\\bar.html", "file:///c:/foo/bar.html"),
        ("file://host/dir/file", "C|", "file://host/C:"),
        ("file://host/D:/dir1/dir2/file", "C|", "file://host/C:"),
        ("file://host/dir/file", "C|#", "file://host/C:#"),
        ("file://host/dir/file", "C|?", "file://host/C:?"),
        ("file://host/dir/file", "C|?q#f", "file://host/C:?q#f"),
        ("file://host/dir/file", "C|\\", "file://host/C:/"),
        ("file://host/dir/file", "C|\n/", "file://host/C:/"),
        ("file://host/", "file:C:/", "file://host/C:/"),
        ("file://host/", "file:/C:/", "file://host/C:/"),
        ("file:///c:/baz/qux", "/c|/foo/bar", "file:///c:/foo/bar"),
        ("file:///c:/baz/qux", "file:\\c:\\foo\\bar", "file:///c:/foo/bar"),
        (
            "file:///tmp/mock/path",
            "  File:c|////foo\\bar.html",
            "file:///c:////foo/bar.html",
        ),
        # Not a drive letter.
        ("file://host/dir/file", "C|a", "file://host/dir/C%7Ca"),
        ("file://host/dir/file", "a|b", "file://host/dir/a%7Cb"),
        ("file://host/dir/file", "C:/x", "c:/x"),
        # An absolute path keeps the drive letter of the base.
        ("file:///C:/a/b", "/", "file:///C:/"),
        ("file://h/C:/a/b", "/", "file://h/C:/"),
        ("file:///C:/a/b", "/x/../..", "file:///C:/"),
        ("file:///C:/a/b", "/D:/x", "file:///D:/x"),
        ("file:///C|a/b", "/x", "file:///x"),
        ("file:///", "/x", "file:///x"),
        # ".." does not remove it.
        ("file:///C:/", "..", "file:///C:/"),
        ("file://x/C:/", "..", "file://x/C:/"),
        ("file:///C:/a/b", "../../..", "file:///C:/"),
        ("file:///C:", "..", "file:///C:/"),
        ("file:///C:", "x", "file:///C:/x"),
        ("file:c:/a", "b", "file:///c:/b"),
        ("file://h", "x", "file://h/x"),
        ("file://h/a/b", "c", "file://h/a/c"),
        # A drive letter in the authority is the start of the path.
        ("file:///C:/a/b", "//d:", "file:///d:"),
        ("file:///C:/a/b", "//d:/..", "file:///d:/"),
        ("file://host/", "//C:/", "file:///C:/"),
        ("file://host/", "file://C:/", "file:///C:/"),
        ("file:///tmp/mock/path", "//C|/foo/bar", "file:///C:/foo/bar"),
        ("file:///tmp/mock/path", "\\\\C|\\foo", "file:///C:/foo"),
        # Other schemes read "//d:" as a host.
        ("http://h/a", "//d:", "http://d"),
        ("http://h/a", "/C|/x", "http://h/C%7C/x"),
        ("sc://h/a", "C|/x", "sc://h/C%7C/x"),
        ("http://h/C:/a", "..", "http://h/"),
    ],
)
def test_join(base: str, reference: str, expected: str) -> None:
    joined = URL(base).join(URL(reference))
    assert str(joined) == expected
    assert joined == URL(expected)


@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        ("file:///C:/", "..", "file:///"),
        ("file:///C:/a/b", "/", "file:///"),
        ("file:///C:/a/b", "//d:", "file://d"),
        ("file:///tmp/mock/path", "file:c:/foo", "file:c:/foo"),
    ],
)
def test_join_rfc(base: str, reference: str, expected: str) -> None:
    joined = URL(base, mode="rfc").join(URL(reference, mode="rfc"))
    assert str(joined) == expected


@pytest.mark.parametrize("base", ["http://h/", "sc://h/"])
@pytest.mark.parametrize("reference", ["//C|/x", "\\\\C|\\x"])
def test_join_pipe_authority_rejected(base: str, reference: str) -> None:
    with pytest.raises(ValueError, match="drive letter for an authority"):
        URL(base).join(URL(reference))


def test_pipe_authority_reference() -> None:
    reference = URL("//C|/x")
    assert str(reference) == "///C:/x"
    assert reference.raw_host is None


def test_reference_keeps_drive_letter() -> None:
    base = URL("file://host/dir/file")
    reference = URL("C|").with_query("q").with_fragment("f")
    assert str(base.join(reference)) == "file://host/C:?q#f"
    unpickled = pickle.loads(pickle.dumps(URL("//C|/x")))
    assert str(base.join(unpickled)) == "file:///C:/x"


@pytest.mark.parametrize(
    ("kwargs", "whatwg", "rfc"),
    [
        ({"authority": "C:", "path": "/x"}, "file:///C:/x", "file://c/x"),
        ({"authority": "C|", "path": "/x/.."}, "file:///C:/", None),
        ({"authority": "c:"}, "file:///c:", "file://c"),
        ({"path": "/C|/x/../.."}, "file:///C:/", None),
        ({"path": "/C:/a/../.."}, "file:///C:/", "file:/"),
        ({"path": "C|/a/../.."}, "file:///C:/", None),
        ({"path": ".//p"}, "file:////p", "file:/p"),
        ({"host": "h", "path": "/C:/.."}, "file://h/C:/", "file://h/"),
        ({"host": "h", "path": "/C|/x"}, "file://h/C:/x", None),
        ({"host": "h", "path": "/a/C|"}, "file://h/a/C%7C", None),
    ],
)
def test_build(kwargs: BuildArgs, whatwg: str, rfc: str | None) -> None:
    built = URL.build(scheme="file", **kwargs)
    assert str(built) == whatwg
    assert built == URL(whatwg)
    if rfc is not None:
        assert str(URL.build(scheme="file", mode="rfc", **kwargs)) == rfc


def test_build_drive_authority_needs_absolute_path() -> None:
    with pytest.raises(ValueError, match="should start with a slash"):
        URL.build(scheme="file", authority="C:", path="x")


def test_build_other_scheme() -> None:
    assert str(URL.build(scheme="http", host="h", path="/C:/..")) == "http://h/"
    assert str(URL.build(scheme="http", host="h", path="/C|")) == "http://h/C%7C"


@pytest.mark.parametrize(
    ("url", "path", "expected"),
    [
        ("file:///x", "/C|/a/../..", "file:///C:/"),
        ("file://h/x", "C|", "file://h/C:"),
        ("file:///C:/x", "/a/..", "file:///"),
        ("file:///x", "a/b/..", "file:///a/"),
        ("file:///x", "/a|b", "file:///a%7Cb"),
        ("http://h/x", "/C|/..", "http://h/"),
        ("sc:x", "C|", "sc:/C%7C"),
    ],
)
def test_with_path(url: str, path: str, expected: str) -> None:
    replaced = URL(url).with_path(path)
    assert str(replaced) == expected
    assert replaced == URL(expected)


def test_with_path_encoded() -> None:
    url = URL("file:///x").with_path("/C|/..", encoded=True)
    assert url.raw_path == "/C|/.."


def test_with_path_rfc() -> None:
    url = URL("file:///x", mode="rfc").with_path("/C:/a/../..")
    assert str(url) == "file:///"


@pytest.mark.parametrize(
    ("url", "segments", "expected"),
    [
        ("file:///", ("C|",), "file:///C:"),
        ("file://", ("C|", "x"), "file:///C:/x"),
        ("file://h/", ("C|/x", "y"), "file://h/C:/x/y"),
        ("file:///", ("C|a",), "file:///C%7Ca"),
        ("file:///a", ("C|",), "file:///a/C%7C"),
        ("file:///C:/", ("..",), "file:///C:/"),
        ("file:///C:/a", ("..", "..", "x"), "file:///C:/x"),
        ("file://h/C:", ("..",), "file://h/C:/"),
        ("http://h/C:/", ("..",), "http://h/"),
    ],
)
def test_joinpath(url: str, segments: tuple[str, ...], expected: str) -> None:
    joined = URL(url).joinpath(*segments)
    assert str(joined) == expected
    assert joined == URL(expected)


def test_truediv() -> None:
    assert str(URL("file:///") / "C|" / ".." / "x") == "file:///C:/x"
    assert str(URL("file:///", mode="rfc") / "C:" / "..") == "file:///"
    assert URL("file:///").joinpath("C|", encoded=True).raw_path == "/C|"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file:///C:/a/b", "file:///C:/a"),
        ("file:///C:/a", "file:///C:"),
        ("file:///C:/", "file:///C:"),
    ],
)
def test_parent(url: str, expected: str) -> None:
    assert str(URL(url).parent) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc://C:/x", "file:///C:/x"),
        ("sc://C:/x/../..", "file:///C:/"),
        ("sc://C:", "file:///C:"),
    ],
)
def test_with_scheme(url: str, expected: str) -> None:
    moved = URL(url, encoded=True).with_scheme("file")
    assert str(moved) == expected
    assert moved == URL(expected)


def test_mode_change() -> None:
    url = URL("file://C:/x", encoded=True, mode="rfc")
    assert str(url) == "file://C:/x"
    assert str(URL(url, mode="whatwg")) == "file:///C:/x"


def test_with_host_is_a_host() -> None:
    with pytest.raises(ValueError, match="cannot contain"):
        URL("file://h/x").with_host("C:")
