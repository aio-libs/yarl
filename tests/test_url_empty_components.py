"""An empty authority, query or fragment is kept apart from an absent one.

RFC 3986 section 5.3 and the WHATWG URL Standard both keep "http://h/p?"
distinct from "http://h/p", and "sc:///p" distinct from "sc:/p".
"""

import operator
import pickle
from collections.abc import Callable

import pytest

from yarl import URL


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/p?",
        "http://example.com/p#",
        "http://example.com/p?#",
        "http://example.com/p?q#",
        "http://example.com/p?#f",
        "sc://",
        "sc://?",
        "sc://#",
        "sc:///p",
        "data:///test",
        "mailto:///test",
        "gopher:/example.com/",
        "gopher:example.com/",
        "file:///C:/",
        "//",
        "//?",
        "?",
        "#",
    ],
)
def test_round_trip(url: str) -> None:
    assert str(URL(url)) == url
    assert URL(str(URL(url))) == URL(url)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("http://example.com/p?", "http://example.com/p"),
        ("http://example.com/p#", "http://example.com/p"),
        ("http://example.com/p?", "http://example.com/p#"),
        ("sc:///p", "sc:/p"),
        ("sc://", "sc:"),
    ],
)
def test_empty_differs_from_absent(first: str, second: str) -> None:
    assert URL(first) != URL(second)
    assert len({URL(first), URL(second)}) == 2


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("http://example.com/p", "http://example.com/p?"),
        ("http://example.com/p", "http://example.com/p#"),
        ("sc:/p", "sc:///p"),
    ],
)
@pytest.mark.parametrize(
    ("op", "expected"),
    [
        (operator.lt, (True, False, False)),
        (operator.le, (True, False, True)),
        (operator.gt, (False, True, False)),
        (operator.ge, (False, True, True)),
    ],
)
def test_ordering(
    first: str,
    second: str,
    op: Callable[[URL, URL], bool],
    expected: tuple[bool, bool, bool],
) -> None:
    # A URL without the empty component sorts before the one with it; each
    # operator runs once per case, on (first, second), (second, first) and
    # a URL against an equal copy of itself.
    lower, higher = URL(first), URL(second)
    assert (
        op(lower, higher),
        op(higher, lower),
        op(higher, URL(second)),
    ) == expected


def test_special_scheme_empty_authority_ignored() -> None:
    # "file:" URLs always print "//", so the two forms are the same URL.
    first, second = URL("file:/path"), URL("file:///path")
    assert first == second
    assert hash(first) == hash(second)
    assert str(first) == str(second) == "file:///path"


def test_path_starting_with_double_slash() -> None:
    url = URL("non-spec:/.//path")
    assert url.raw_path == "//path"
    assert str(url) == "non-spec:/.//path"
    assert str(URL.build(path="//a")) == "/.//a"
    assert URL("sc:////path").raw_path == "//path"
    assert str(URL("sc:////path")) == "sc:////path"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://example.com?", "http://example.com/?"),
        ("http://example.com:80/p?", "http://example.com/p?"),
        ("sc:/p?", "sc:/p?"),
        ("non-spec:/.//p#", "non-spec:/.//p#"),
    ],
)
def test_str_with_empty_components(url: str, expected: str) -> None:
    assert str(URL(url)) == expected


def test_with_fragment_none_keeps_other_empty_components() -> None:
    url = URL("http://example.com/p?")
    assert url.with_fragment(None) is url


def test_bool() -> None:
    assert URL("?")
    assert URL("#")
    assert not URL("")


def test_raw_path_qs() -> None:
    url = URL("http://example.com/p?")
    assert url.raw_path_qs == "/p?"
    assert url.path_qs == "/p?"
    assert URL("http://example.com?").raw_path_qs == "/?"


def test_raw_parts_empty_authority() -> None:
    assert URL("sc://").raw_parts == ("/",)
    assert URL("sc:///a").raw_parts == ("/", "a")


def test_origin_drops_empty_components() -> None:
    url = URL("http://example.com?#")
    assert str(url.origin()) == "http://example.com"
    assert url.origin() == URL("http://example.com")


def test_relative_keeps_empty_components() -> None:
    assert str(URL("http://example.com/p?#").relative()) == "/p?#"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc:///a/b?#", "sc:///a"),
        ("sc:///?", "sc:///"),
        ("sc:///", "sc:///"),
    ],
)
def test_parent(url: str, expected: str) -> None:
    assert str(URL(url).parent) == expected


def test_parent_without_empty_components_is_self() -> None:
    url = URL("sc:///")
    assert url.parent is url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc://", "sc:///a"),
        ("sc:///x?#", "sc:///x/a"),
        ("sc:///x/./y", "sc:///x/a"),
    ],
)
def test_make_child(url: str, expected: str) -> None:
    child = URL(url) / ".." / "a" if "./" in url else URL(url) / "a"
    assert str(child) == expected


def test_with_name_and_suffix() -> None:
    assert str(URL("sc://").with_name("n")) == "sc:///n"
    assert str(URL("sc:///a/b?#").with_suffix(".x")) == "sc:///a/b.x"
    url = URL("sc:///a/b?#").with_name("c", keep_query=True, keep_fragment=True)
    assert str(url) == "sc:///a/c?#"
    url = URL("sc:///a/b?#").with_suffix(".x", keep_query=True)
    assert str(url) == "sc:///a/b.x?"


def test_with_path() -> None:
    url = URL("http://example.com/p?#")
    assert str(url.with_path("/q")) == "http://example.com/q"
    assert str(url.with_path("/q", keep_query=True)) == "http://example.com/q?"
    assert str(url.with_path("/q", keep_fragment=True)) == "http://example.com/q#"


def test_modifiers_keep_empty_components() -> None:
    url = URL("sc://?#")
    assert str(url.with_scheme("tc")) == "tc://?#"
    url = URL("http://example.com/p?#")
    assert str(url.with_user("u")) == "http://u@example.com/p?#"
    assert str(url.with_password("pw")) == "http://:pw@example.com/p?#"
    assert str(url.with_host("other.com")) == "http://other.com/p?#"
    assert str(url.with_port(8080)) == "http://example.com:8080/p?#"


def test_query_modifiers() -> None:
    url = URL("http://example.com/p?")
    assert str(url.with_query(None)) == "http://example.com/p"
    assert str(url.with_query(a=1)) == "http://example.com/p?a=1"
    assert str(url.extend_query(a=1)) == "http://example.com/p?a=1"
    assert str(url.update_query({})) == "http://example.com/p?"
    assert str(url.update_query(a=1)) == "http://example.com/p?a=1"
    assert str(url.update_query(None)) == "http://example.com/p"


def test_with_fragment() -> None:
    url = URL("http://example.com/p#")
    assert str(url.with_fragment(None)) == "http://example.com/p"
    assert str(url.with_fragment("x")) == "http://example.com/p#x"
    plain = URL("http://example.com/p")
    assert plain.with_fragment(None) is plain


def test_human_repr() -> None:
    assert URL("http://example.com/p?#").human_repr() == "http://example.com/p?#"


@pytest.mark.parametrize(
    ("base", "reference", "expected"),
    [
        ("http://example.org/foo/bar", "#", "http://example.org/foo/bar#"),
        ("http://example.org/foo/bar", "?", "http://example.org/foo/bar?"),
        ("http://example.org/foo/bar?q", "?", "http://example.org/foo/bar?"),
        ("http://example.org/foo/bar?", "", "http://example.org/foo/bar?"),
        ("http://example.org/foo/bar?", "#f", "http://example.org/foo/bar?#f"),
        ("http://example.org/foo/bar", "foo://", "foo://"),
        ("file://host/", "///C:/", "file:///C:/"),
        # http needs a host, so an empty reference authority is not taken.
        ("http://example.com/x", "///a", "http://example.com/a"),
        ("file://host/", "file:///C:/", "file:///C:/"),
        ("sc:///pa/pa", "i", "sc:///pa/i"),
        ("sc:///pa/pa", "?i", "sc:///pa/pa?i"),
        ("sc://x/", "///", "sc:///"),
        ("sc://x/", "////x/", "sc:////x/"),
        ("a://", "b.html", "a:///b.html"),
        ("non-spec:/p", "/.//path", "non-spec:/.//path"),
    ],
)
def test_join(base: str, reference: str, expected: str) -> None:
    assert str(URL(base).join(URL(reference))) == expected


@pytest.mark.parametrize("url", ["http://example.com/p?#", "sc://", "http://h/p"])
def test_pickle_round_trip(url: str) -> None:
    u = URL(url)
    v = pickle.loads(pickle.dumps(u))
    assert v == u
    assert str(v) == url


@pytest.mark.parametrize(
    "state", [(("sc", "", "/p", "", ""),), (("sc", "", "/p", "", ""), "rfc")]
)
def test_setstate_without_empty_mask(state: tuple[object, ...]) -> None:
    # Pickles made by older yarl releases have no mask of empty components.
    url = URL()
    url.__setstate__(state)
    assert str(url) == "sc:/p"


def test_pickle_keeps_mode() -> None:
    url = URL("sc://?", mode="rfc")
    loaded = pickle.loads(pickle.dumps(url))
    assert loaded.mode == "rfc"
    assert str(loaded) == "sc://?"


def test_mode_change_keeps_empty_components() -> None:
    url = URL(URL("http://example.com/p?#"), mode="rfc")
    assert str(url) == "http://example.com/p?#"
    base = URL("sc:///a", mode="rfc")
    assert str(base.join(URL("b?"))) == "sc:///b?"


# WHATWG always writes "//" for a special scheme; RFC 3986 only when the
# URL has an authority.
@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        ("http:/x", "http:///x", "http:/x"),
        ("file:/p", "file:///p", "file:/p"),
        ("file:///p", "file:///p", "file:///p"),
        ("gopher:/x", "gopher:/x", "gopher:/x"),
    ],
)
def test_special_scheme_authority_by_mode(url: str, whatwg: str, rfc: str) -> None:
    assert str(URL(url)) == whatwg
    assert str(URL(url, mode="rfc")) == rfc
    assert URL(url, mode="rfc").human_repr() == rfc


def test_build_special_scheme_by_mode() -> None:
    assert str(URL.build(scheme="file", path="/p")) == "file:///p"
    assert str(URL.build(scheme="file", path="/p", mode="rfc")) == "file:/p"


# URLs are equal exactly when they print the same: RFC mode prints the
# empty authority of a special scheme, WHATWG mode always prints "//".
@pytest.mark.parametrize(
    ("first", "second", "equal"),
    [
        (URL("file:/p"), URL("file:///p"), True),
        (URL("http:/x"), URL("http:///x"), True),
        (URL("file:/p", mode="rfc"), URL("file:///p", mode="rfc"), False),
        (URL("http:/x", mode="rfc"), URL("http:///x", mode="rfc"), False),
        (URL("file:/p"), URL("file:///p", mode="rfc"), True),
        (URL("http:/x"), URL("http:/x", mode="rfc"), False),
        (URL("http://h/p?"), URL("http://h/p?", mode="rfc"), True),
    ],
)
def test_equality_follows_str(first: URL, second: URL, equal: bool) -> None:
    assert (str(first) == str(second)) is equal
    assert (first == second) is equal
    if equal:
        assert hash(first) == hash(second)
    assert len({first: 1, second: 2}) == (1 if equal else 2)


@pytest.mark.parametrize(
    ("path", "written"),
    [
        ("//a", "sc:/.//a"),
        ("//a/b", "sc:/.//a/b"),
        ("/.//a", "sc:/././/a"),
        ("/././/a", "sc:/./././/a"),
        ("/./a", "sc:/./a"),
        ("/..//a", "sc:/..//a"),
    ],
)
def test_path_starting_with_double_slash_round_trips(path: str, written: str) -> None:
    # str() adds "/." in front of a path that would read as an authority,
    # including a literal "/." before "//", and parsing drops exactly one.
    url = URL.build(scheme="sc", path=path, encoded=True)
    assert str(url) == written
    for encoded in (True, False):
        again = URL(written, encoded=encoded)
        assert again.raw_path == path
        assert again.raw_parts == url.raw_parts


def test_long_dot_segment_run_round_trips() -> None:
    # The "/." run is matched in one pass, not by copying the path per step.
    path = "/." * 50_000 + "//a"
    url = URL.build(scheme="sc", path=path, encoded=True)
    assert str(url) == f"sc:/.{path}"
    assert URL(str(url), encoded=True).raw_path == path
    assert URL(str(url)).raw_path == path
