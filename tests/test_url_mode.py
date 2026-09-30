import pickle
from collections.abc import Callable
from urllib.parse import SplitResult

import pytest

from yarl import URL, Mode

RFC = Mode.RFC
WHATWG = Mode.WHATWG


def test_enum_values() -> None:
    assert RFC == "rfc"
    assert WHATWG == "whatwg"
    assert str(RFC) == "rfc"
    assert f"{WHATWG}" == "whatwg"
    assert Mode.__module__ == "yarl"


def test_default_is_whatwg() -> None:
    assert URL("http://example.com/").mode is WHATWG
    assert URL.build(scheme="http", host="example.com").mode is WHATWG


@pytest.mark.parametrize(
    ("mode", "expected"),
    [("rfc", RFC), ("whatwg", WHATWG), (RFC, RFC), (WHATWG, WHATWG)],
)
def test_accepted_values(mode: Mode, expected: Mode) -> None:
    assert URL("http://example.com/", mode=mode).mode is expected
    url = URL.build(scheme="http", host="example.com", mode=mode)
    assert url.mode is expected


@pytest.mark.parametrize("mode", ["RFC", "WHATWG", "http", "", 1, [], ["rfc"]])
def test_invalid_value(mode: object) -> None:
    with pytest.raises(ValueError, match="is not a valid Mode"):
        URL("http://example.com/", mode=mode)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="is not a valid Mode"):
        URL.build(scheme="http", host="example.com", mode=mode)  # type: ignore[arg-type]


def test_change_mode_through_constructor() -> None:
    url = URL("http://example.com/path?a=1#frag")
    rfc_url = URL(url, mode="rfc")
    assert rfc_url.mode is RFC
    assert rfc_url == url
    assert str(rfc_url) == str(url)
    back = URL(rfc_url)
    assert back.mode is WHATWG
    assert back == url


def test_same_mode_returns_same_object() -> None:
    url = URL("http://example.com/", mode="rfc")
    assert URL(url, mode=RFC) is url
    whatwg_url = URL("http://example.com/")
    assert URL(whatwg_url) is whatwg_url


def test_str_subclass() -> None:
    class S(str):
        pass

    assert URL(S("http://example.com/"), mode="rfc").mode is RFC
    assert URL(S("http://example.com/"), encoded=True, mode="rfc").mode is RFC


def test_encoded() -> None:
    assert URL("http://example.com/%41", encoded=True, mode="rfc").mode is RFC
    split = SplitResult("http", "example.com", "/", "", "")
    assert URL(split, encoded=True, mode="rfc").mode is RFC
    assert URL(split, encoded=True).mode is WHATWG
    url = URL.build(scheme="http", host="example.com", encoded=True, mode="rfc")
    assert url.mode is RFC


def test_cache_does_not_leak_mode() -> None:
    s = "http://cache-mode.example/path"
    assert URL(s).mode is WHATWG
    assert URL(s, mode="rfc").mode is RFC
    assert URL(s).mode is WHATWG
    assert URL(s, encoded=True).mode is WHATWG
    assert URL(s, encoded=True, mode="rfc").mode is RFC


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
        pytest.param(lambda u: u.join(URL("other", mode="rfc")), id="join"),
        pytest.param(
            lambda u: u.join(URL("ftp://host/", mode="rfc")), id="join-absolute"
        ),
    ],
)
def test_derived_urls_keep_mode(derive: Callable[[URL], URL]) -> None:
    url = URL("http://example.com/dir/file?a=1#frag", mode="rfc")
    derived = derive(url)
    assert derived.mode is RFC
    assert derived == derive(URL(url, mode="whatwg"))


@pytest.mark.parametrize(
    ("base", "ref", "expected"),
    [
        ("rfc", "whatwg", RFC),
        ("whatwg", "rfc", WHATWG),
    ],
)
@pytest.mark.parametrize("reference", ["other?q=1", "ftp://host/path"])
def test_join_takes_mode_from_base(
    base: Mode, ref: Mode, expected: Mode, reference: str
) -> None:
    base_url = URL("http://example.com/dir/file", mode=base)
    ref_url = URL(reference, mode=ref)
    joined = base_url.join(ref_url)
    assert joined.mode is expected
    assert joined == URL(base_url, mode=ref).join(ref_url)


def test_join_absolute_reference_same_mode_is_identity() -> None:
    ref = URL("ftp://host/path", mode="rfc")
    assert URL("http://example.com/", mode="rfc").join(ref) is ref


def test_equality_and_hash_ignore_mode() -> None:
    whatwg_url = URL("http://example.com/path")
    rfc_url = URL("http://example.com/path", mode="rfc")
    assert whatwg_url == rfc_url
    assert hash(whatwg_url) == hash(rfc_url)
    assert not whatwg_url < rfc_url
    assert whatwg_url <= rfc_url


def test_repr() -> None:
    assert repr(URL("http://example.com/")) == "URL('http://example.com/')"
    rfc_url = URL("http://example.com/", mode="rfc")
    assert repr(rfc_url) == "URL('http://example.com/', mode='rfc')"


@pytest.mark.parametrize("mode", [RFC, WHATWG])
def test_pickle_round_trip(mode: Mode) -> None:
    url = URL("http://example.com/path?a=1#frag", mode=mode)
    loaded = pickle.loads(pickle.dumps(url))
    assert loaded == url
    assert loaded.mode is mode
    assert url.__getstate__()[1] == mode.value


def test_unpickle_old_state_is_whatwg() -> None:
    val = ("http", "example.com", "/path", "", "")
    u = URL.__new__(URL)
    u.__setstate__((val,))
    assert u._val == val
    assert u.mode is WHATWG


def test_unpickle_default_style_state_is_whatwg() -> None:
    val = ("http", "example.com", "/path", "", "")
    u = URL.__new__(URL)
    u.__setstate__((None, {"_val": val}))
    assert u._val == val
    assert u.mode is WHATWG


# RFC 3986 userinfo cannot contain "@"; WHATWG percent-encodes all but the
# last one.
@pytest.mark.parametrize(
    ("url", "whatwg"),
    [
        ("http://a@b@example.com/", "http://a%40b@example.com/"),
        ("sc://a:b@c@example.com/", "sc://a:b%40c@example.com/"),
    ],
)
def test_at_sign_in_userinfo(url: str, whatwg: str) -> None:
    assert str(URL(url)) == whatwg
    with pytest.raises(ValueError, match="userinfo cannot contain '@'"):
        URL(url, mode=RFC)


def test_at_sign_in_userinfo_rejected_by_build() -> None:
    with pytest.raises(ValueError, match="userinfo cannot contain '@'"):
        URL.build(scheme="http", authority="a@b@example.com", mode=RFC)
    url = URL.build(scheme="http", authority="a@b@example.com")
    assert str(url) == "http://a%40b@example.com"


def test_rfc_mode_empty_host_with_at_sign_rejected() -> None:
    with pytest.raises(ValueError):
        URL("sc://us@er:pw@/", mode=RFC)


# RFC 3987 encodes internationalized hosts with IDNA2008, which disallows
# emoji; WHATWG uses UTS #46, which accepts them.
@pytest.mark.parametrize("host", ["💩", "💩.example", "💩.123"])
def test_idna2008_host_in_rfc_mode(host: str) -> None:
    with pytest.raises(ValueError, match="not a valid IDNA2008 name"):
        URL(f"http://{host}/", mode=RFC)
    with pytest.raises(ValueError, match="not a valid IDNA2008 name"):
        URL.build(scheme="http", host=host, mode=RFC)
    with pytest.raises(ValueError, match="not a valid IDNA2008 name"):
        URL.build(scheme="http", authority=f"user@{host}", mode=RFC)
    with pytest.raises(ValueError, match="not a valid IDNA2008 name"):
        URL("http://example.com/", mode=RFC).with_host(host)


def test_idna2008_host_in_whatwg_mode() -> None:
    assert str(URL("http://💩.example/")) == "http://xn--ls8h.example/"
    assert URL("http://example.com/").with_host("💩").raw_host == "xn--ls8h"


@pytest.mark.parametrize("mode", [RFC, WHATWG])
def test_idna2008_host_accepted(mode: Mode) -> None:
    url = URL("http://ñ.example/", mode=mode)
    assert url.raw_host == "xn--ida.example"


def test_zone_identifier_not_idna_encoded() -> None:
    # A zone identifier is not a host name, so IDNA does not apply to it.
    # RFC 3986 mode rejects it: an IP-literal is ASCII in RFC 3987 too.
    assert URL("http://[fe80::1%25ñ]/").raw_host == "fe80::1%25ñ"
    with pytest.raises(ValueError, match="'ñ' in the host"):
        URL("http://[fe80::1%25ñ]/", mode=RFC)


@pytest.mark.parametrize("first", [RFC, WHATWG])
def test_idna2008_check_shares_host_cache(first: Mode) -> None:
    # The host encoding cache is shared by both modes; the IDNA2008 flag is
    # cached with it, so the order of the calls does not matter.
    host = "💩-cache.example"
    for mode in (first, RFC if first is WHATWG else WHATWG):
        if mode is RFC:
            with pytest.raises(ValueError, match="not a valid IDNA2008 name"):
                URL.build(scheme="http", host=host, mode=mode)
        else:
            url = URL.build(scheme="http", host=host, mode=mode)
            assert url.raw_host == "xn---cache-hx54e.example"
