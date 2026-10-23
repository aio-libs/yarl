"""IPvFuture hosts, RFC 3986 section 3.2.2.

``IP-literal = "[" ( IPv6address / IPvFuture ) "]"`` with
``IPvFuture = "v" 1*HEXDIG "." 1*( unreserved / sub-delims / ":" )``.
The brackets are part of the host: without them ``v1.x`` is a reg-name,
so an IPvFuture host keeps them in ``raw_host`` and ``host``, unlike an
IPv6 address. The WHATWG URL Standard has no IPvFuture, its host parser
reads any ``[...]`` as an IPv6 address, so WHATWG mode rejects one.
"""

import pickle

import pytest

from yarl import URL

WHATWG_ERROR = "IPvFuture address, which the WHATWG URL Standard does not have"


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://[v1.x]/", "http://[v1.x]/"),
        ("http://[v1.x]:80/", "http://[v1.x]/"),
        ("http://[v1.x]:8080/p", "http://[v1.x]:8080/p"),
        ("foo://[v1.x]/", "foo://[v1.x]/"),
        ("http://u:p@[v1f.a:b]:81/", "http://u:p@[v1f.a:b]:81/"),
        ("//[v7.!$&'()*+,;=-._~]/", "//[v7.!$&'()*+,;=-._~]/"),
    ],
)
def test_parse_keeps_brackets(url: str, expected: str, encoded: bool) -> None:
    u = URL(url, mode="rfc", encoded=encoded)
    assert str(u) == expected
    assert str(URL(str(u), mode="rfc")) == expected


def test_equal_after_round_trip() -> None:
    u = URL("http://[v1.x]:8080/p", mode="rfc")
    assert URL(str(u), mode="rfc") == u
    assert hash(URL(str(u), mode="rfc")) == hash(u)


def test_parse_lowercases() -> None:
    u = URL("http://[V1F.A:B]/", mode="rfc")
    assert str(u) == "http://[v1f.a:b]/"


def test_parse_encoded_keeps_case() -> None:
    u = URL("http://[V1F.A:B]/", mode="rfc", encoded=True)
    assert str(u) == "http://[V1F.A:B]/"


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize(
    "url",
    [
        "http://[v1.x%41]/",
        "http://[v1.]/",
        "http://[vg.x]/",
        "http://[v.x]/",
    ],
)
def test_parse_invalid(url: str, encoded: bool) -> None:
    with pytest.raises(ValueError, match="IPvFuture address is invalid"):
        URL(url, mode="rfc", encoded=encoded)


def test_host_properties() -> None:
    u = URL("http://[v1.x]:8080/", mode="rfc")
    assert u.raw_host == "[v1.x]"
    assert u.host == "[v1.x]"
    assert u.host_subcomponent == "[v1.x]"
    assert u.host_port_subcomponent == "[v1.x]:8080"
    assert u.authority == "[v1.x]:8080"
    assert u.raw_authority == "[v1.x]:8080"
    assert u.port == 8080
    assert u.explicit_port == 8080


def test_host_properties_with_colon() -> None:
    u = URL("http://[v1.a:b]:80/", mode="rfc", encoded=True)
    assert u.raw_host == "[v1.a:b]"
    assert u.host == "[v1.a:b]"
    assert u.host_subcomponent == "[v1.a:b]"
    assert u.host_port_subcomponent == "[v1.a:b]"
    assert u.authority == "[v1.a:b]:80"
    assert u.port == 80
    assert u.is_default_port()


def test_human_repr() -> None:
    u = URL("http://u@[v1.a:b]:8080/p", mode="rfc")
    assert u.human_repr() == "http://u@[v1.a:b]:8080/p"


def test_pickle() -> None:
    u = URL("http://[v1.x]:8080/", mode="rfc")
    v = pickle.loads(pickle.dumps(u))
    assert v == u
    assert v.raw_host == "[v1.x]"
    assert str(v) == "http://[v1.x]:8080/"


def test_with_port() -> None:
    u = URL("http://[v1.a:b]/", mode="rfc")
    assert str(u.with_port(81)) == "http://[v1.a:b]:81/"
    assert str(u.with_port(81).with_port(None)) == "http://[v1.a:b]/"


def test_with_host() -> None:
    u = URL("http://example.com:8080/p", mode="rfc")
    assert str(u.with_host("[V1.a:B]")) == "http://[v1.a:b]:8080/p"
    # Without brackets the same characters are a reg-name.
    assert str(u.with_host("v1.x")) == "http://v1.x:8080/p"


@pytest.mark.parametrize("host", ["[v1.x", "[v1.x%41]", "[vz.x]"])
def test_with_host_invalid(host: str) -> None:
    u = URL("http://example.com/", mode="rfc")
    with pytest.raises(ValueError, match="IPvFuture address is invalid"):
        u.with_host(host)


def test_build_host() -> None:
    u = URL.build(scheme="http", host="[v1.x]", port=80, path="/", mode="rfc")
    assert str(u) == "http://[v1.x]/"
    assert u == URL("http://[v1.x]/", mode="rfc")


def test_build_authority() -> None:
    u = URL.build(scheme="http", authority="u@[V1.X]:81", mode="rfc")
    assert str(u) == "http://u@[v1.x]:81"
    assert u.raw_host == "[v1.x]"


def test_build_encoded() -> None:
    u = URL.build(scheme="http", host="[v1.x]", encoded=True, mode="rfc")
    assert str(u) == "http://[v1.x]"
    assert u.raw_host == "[v1.x]"


def test_join() -> None:
    base = URL("http://[v1.x]:8080/a/b", mode="rfc")
    assert str(base.join(URL("c", mode="rfc"))) == "http://[v1.x]:8080/a/c"
    other = URL("http://example.com/", mode="rfc")
    assert str(other.join(URL("//[v1.x]/c", mode="rfc"))) == "http://[v1.x]/c"


def test_origin() -> None:
    u = URL("http://u:p@[v1.x]:8080/p?q#f", mode="rfc")
    assert str(u.origin()) == "http://[v1.x]:8080"


@pytest.mark.parametrize(
    "url", ["http://[v1.x]/", "foo://[v1.x]/", "//u@[V1F.A:B]:80/"]
)
def test_whatwg_rejects(url: str) -> None:
    with pytest.raises(ValueError, match=WHATWG_ERROR):
        URL(url)


def test_whatwg_pre_encoded() -> None:
    # A pre-encoded URL is taken as is, as with other hosts, but its host
    # is checked once it moves under a special scheme.
    u = URL("foo://[v1.x]/", encoded=True)
    assert str(u) == "foo://[v1.x]/"
    with pytest.raises(ValueError, match=WHATWG_ERROR):
        u.with_scheme("http")


def test_whatwg_build_rejects() -> None:
    with pytest.raises(ValueError, match=WHATWG_ERROR):
        URL.build(scheme="foo", host="[v1.x]")
    with pytest.raises(ValueError, match=WHATWG_ERROR):
        URL.build(scheme="foo", authority="[v1.x]:80")


def test_whatwg_with_host_rejects() -> None:
    with pytest.raises(ValueError, match=WHATWG_ERROR):
        URL("foo://example.com/").with_host("[v1.x]")


@pytest.mark.parametrize("url", ["http://[v1.x]/", "foo://[v1.x]/"])
def test_mode_change_to_whatwg_rejects(url: str) -> None:
    u = URL(url, mode="rfc")
    with pytest.raises(ValueError, match=WHATWG_ERROR):
        URL(u, mode="whatwg")


def test_whatwg_join_rejects_rfc_reference() -> None:
    base = URL("foo://example.com/")
    with pytest.raises(ValueError, match=WHATWG_ERROR):
        base.join(URL("//[v1.x]/", mode="rfc"))


def test_ipv6_unaffected() -> None:
    u = URL("foo://[::1]:8080/", mode="rfc")
    assert u.raw_host == "::1"
    assert str(URL(u, mode="whatwg")) == "foo://[::1]:8080/"
