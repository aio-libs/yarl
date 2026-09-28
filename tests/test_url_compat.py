import pickle
from collections.abc import Callable
from urllib.parse import SplitResult

import pytest

from yarl import URL, Compatibility

RFC = Compatibility.RFC
WHATWG = Compatibility.WHATWG


def test_enum_values() -> None:
    assert RFC == "rfc"
    assert WHATWG == "whatwg"
    assert str(RFC) == "rfc"
    assert f"{WHATWG}" == "whatwg"
    assert Compatibility.__module__ == "yarl"


def test_default_is_whatwg() -> None:
    assert URL("http://example.com/").compat is WHATWG
    assert URL.build(scheme="http", host="example.com").compat is WHATWG


@pytest.mark.parametrize(
    ("compat", "expected"),
    [("rfc", RFC), ("whatwg", WHATWG), (RFC, RFC), (WHATWG, WHATWG)],
)
def test_accepted_values(compat: Compatibility, expected: Compatibility) -> None:
    assert URL("http://example.com/", compat=compat).compat is expected
    url = URL.build(scheme="http", host="example.com", compat=compat)
    assert url.compat is expected


@pytest.mark.parametrize("compat", ["RFC", "WHATWG", "http", ""])
def test_invalid_value(compat: str) -> None:
    with pytest.raises(ValueError, match="is not a valid Compatibility"):
        URL("http://example.com/", compat=compat)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="is not a valid Compatibility"):
        URL.build(scheme="http", host="example.com", compat=compat)  # type: ignore[arg-type]


def test_change_compat_through_constructor() -> None:
    url = URL("http://example.com/path?a=1#frag")
    rfc_url = URL(url, compat="rfc")
    assert rfc_url.compat is RFC
    assert rfc_url == url
    assert str(rfc_url) == str(url)
    back = URL(rfc_url)
    assert back.compat is WHATWG
    assert back == url


def test_same_compat_returns_same_object() -> None:
    url = URL("http://example.com/", compat="rfc")
    assert URL(url, compat=RFC) is url
    whatwg_url = URL("http://example.com/")
    assert URL(whatwg_url) is whatwg_url


def test_str_subclass() -> None:
    class S(str):
        pass

    assert URL(S("http://example.com/"), compat="rfc").compat is RFC
    assert URL(S("http://example.com/"), encoded=True, compat="rfc").compat is RFC


def test_encoded() -> None:
    assert URL("http://example.com/%41", encoded=True, compat="rfc").compat is RFC
    split = SplitResult("http", "example.com", "/", "", "")
    assert URL(split, encoded=True, compat="rfc").compat is RFC
    assert URL(split, encoded=True).compat is WHATWG
    url = URL.build(scheme="http", host="example.com", encoded=True, compat="rfc")
    assert url.compat is RFC


def test_cache_does_not_leak_compat() -> None:
    s = "http://cache-compat.example/path"
    assert URL(s).compat is WHATWG
    assert URL(s, compat="rfc").compat is RFC
    assert URL(s).compat is WHATWG
    assert URL(s, encoded=True).compat is WHATWG
    assert URL(s, encoded=True, compat="rfc").compat is RFC


@pytest.mark.parametrize(
    "derive",
    [
        pytest.param(lambda u: u / "child", id="truediv"),
        pytest.param(lambda u: u.joinpath("a", "b"), id="joinpath"),
        pytest.param(lambda u: u % {"b": "2"}, id="mod"),
        pytest.param(lambda u: u.with_scheme("https"), id="with_scheme"),
        pytest.param(lambda u: u.with_user("user"), id="with_user"),
        pytest.param(lambda u: u.with_password("pass"), id="with_password"),
        pytest.param(lambda u: u.with_host("example.org"), id="with_host"),
        pytest.param(lambda u: u.with_port(8080), id="with_port"),
        pytest.param(lambda u: u.with_path("/other"), id="with_path"),
        pytest.param(lambda u: u.with_query(c="3"), id="with_query"),
        pytest.param(lambda u: u.extend_query(c="3"), id="extend_query"),
        pytest.param(lambda u: u.update_query(c="3"), id="update_query"),
        pytest.param(lambda u: u.without_query_params("a"), id="without_query"),
        pytest.param(lambda u: u.with_fragment("other"), id="with_fragment"),
        pytest.param(lambda u: u.with_name("name.txt"), id="with_name"),
        pytest.param(lambda u: u.with_suffix(".txt"), id="with_suffix"),
        pytest.param(lambda u: u.origin(), id="origin"),
        pytest.param(lambda u: u.relative(), id="relative"),
        pytest.param(lambda u: u.parent, id="parent"),
        pytest.param(lambda u: u.join(URL("other", compat="rfc")), id="join"),
        pytest.param(
            lambda u: u.join(URL("ftp://host/", compat="rfc")), id="join-absolute"
        ),
    ],
)
def test_derived_urls_keep_compat(derive: Callable[[URL], URL]) -> None:
    url = URL("http://example.com/dir/file?a=1#frag", compat="rfc")
    derived = derive(url)
    assert derived.compat is RFC
    assert derived == derive(URL(url, compat="whatwg"))


@pytest.mark.parametrize(
    ("base", "ref", "expected"),
    [
        ("rfc", "whatwg", RFC),
        ("whatwg", "rfc", WHATWG),
    ],
)
@pytest.mark.parametrize("reference", ["other?q=1", "ftp://host/path"])
def test_join_takes_compat_from_base(
    base: Compatibility, ref: Compatibility, expected: Compatibility, reference: str
) -> None:
    base_url = URL("http://example.com/dir/file", compat=base)
    ref_url = URL(reference, compat=ref)
    joined = base_url.join(ref_url)
    assert joined.compat is expected
    assert joined == URL(base_url, compat=ref).join(ref_url)


def test_join_absolute_reference_same_compat_is_identity() -> None:
    ref = URL("ftp://host/path", compat="rfc")
    assert URL("http://example.com/", compat="rfc").join(ref) is ref


def test_equality_and_hash_ignore_compat() -> None:
    whatwg_url = URL("http://example.com/path")
    rfc_url = URL("http://example.com/path", compat="rfc")
    assert whatwg_url == rfc_url
    assert hash(whatwg_url) == hash(rfc_url)
    assert not whatwg_url < rfc_url
    assert whatwg_url <= rfc_url


def test_repr() -> None:
    assert repr(URL("http://example.com/")) == "URL('http://example.com/')"
    rfc_url = URL("http://example.com/", compat="rfc")
    assert repr(rfc_url) == "URL('http://example.com/', compat='rfc')"


@pytest.mark.parametrize("compat", [RFC, WHATWG])
def test_pickle_round_trip(compat: Compatibility) -> None:
    url = URL("http://example.com/path?a=1#frag", compat=compat)
    loaded = pickle.loads(pickle.dumps(url))
    assert loaded == url
    assert loaded.compat is compat
    assert url.__getstate__()[1] == compat.value


def test_unpickle_old_state_is_whatwg() -> None:
    val = ("http", "example.com", "/path", "", "")
    u = URL.__new__(URL)
    u.__setstate__((val,))
    assert u._val == val
    assert u.compat is WHATWG


def test_unpickle_default_style_state_is_whatwg() -> None:
    val = ("http", "example.com", "/path", "", "")
    u = URL.__new__(URL)
    u.__setstate__((None, {"_val": val}))
    assert u._val == val
    assert u.compat is WHATWG
