"""WHATWG mode parses the host of a non-special URL as an opaque host."""

import pytest

from yarl import URL, Mode


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        ("sc://faß.ExAmPlE/", "sc://fa%C3%9F.ExAmPlE/", "sc://xn--fa-hia.example/"),
        ("sc://ñ.test/", "sc://%C3%B1.test/", "sc://xn--ida.test/"),
        ("sc://ñ", "sc://%C3%B1", "sc://xn--ida"),
        ("sc://H%4fSt/p", "sc://H%4fSt/p", "sc://h%4fst/p"),
        ("sc://u:p@ÑA:1/", "sc://u:p@%C3%91A:1/", "sc://u:p@xn--a-qga:1/"),
        ("sc://[::1]/", "sc://[::1]/", "sc://[::1]/"),
        ("sc://1.2.3.4/", "sc://1.2.3.4/", "sc://1.2.3.4/"),
    ],
)
def test_parsed(url: str, whatwg: str, rfc: str) -> None:
    assert str(URL(url)) == whatwg
    assert str(URL(url, mode="rfc")) == rfc


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc://%/", "sc://%/"),
        ("sc://\x01\x1f\x7f!/", "sc://%01%1F%7F!/"),
        ("foo://!\"$%&'()*+,-.;=_`{}~/", "foo://!\"$%&'()*+,-.;=_`{}~/"),
    ],
)
def test_outside_rfc_grammar(url: str, expected: str) -> None:
    assert str(URL(url)) == expected
    with pytest.raises(ValueError):
        URL(url, mode="rfc")


@pytest.mark.parametrize("char", "\x00 #/<>?@[\\]^|")
def test_forbidden_host_code_point(char: str) -> None:
    with pytest.raises(ValueError, match="cannot contain"):
        URL("sc://h").with_host(f"a{char}b")


def test_ipvfuture_rejected() -> None:
    with pytest.raises(ValueError, match="IPvFuture"):
        URL("sc://[v1.x]/")


@pytest.mark.parametrize(
    ("raw_host", "host"),
    [
        ("%C3%B1", "ñ"),
        ("Ex%41%c3%b1", "Ex%41ñ"),
        ("a%FF%C3%B1%E2%82", "a%FFñ%E2%82"),
        ("%", "%"),
        ("a%251", "a%251"),
    ],
)
def test_host(raw_host: str, host: str) -> None:
    url = URL(f"sc://{raw_host}/")
    assert url.raw_host == raw_host
    assert url.host_subcomponent == raw_host
    assert url.host == host
    assert url.with_host(host).host == host


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc://%C3%B1/", "sc://ñ/"),
        # The NFKC form of U+FF0F is "/", which URL() rejects in a host.
        ("sc://a%EF%BC%8Fb/", "sc://a%EF%BC%8Fb/"),
    ],
)
def test_human_repr_host(url: str, expected: str) -> None:
    assert URL(url).human_repr() == expected
    assert URL(expected) == URL(url)


def test_host_ipv6() -> None:
    assert URL("sc://[fe80::1%25eth0]/").host == "fe80::1%eth0"


def test_host_rfc_mode() -> None:
    assert URL("sc://ñ", mode="rfc").host == "ñ"


def test_host_encoded() -> None:
    url = URL("sc://Xn--Ida/", encoded=True)
    assert url.raw_host == "Xn--Ida"
    assert url.host == "Xn--Ida"


def test_relative_reference_host_is_a_domain() -> None:
    # Without a scheme there is no telling if the host is opaque.
    assert str(URL("//Ñ/x")) == "//xn--ida/x"


def test_build_host() -> None:
    assert str(URL.build(scheme="sc", host="Ñ")) == "sc://%C3%91"
    assert str(URL.build(scheme="sc", host="::1")) == "sc://[::1]"
    url = URL.build(scheme="sc", host="Ñ", mode="rfc")
    assert str(url) == "sc://xn--ida"


def test_build_authority() -> None:
    url = URL.build(scheme="sc", authority="u@Ñ:1")
    assert str(url) == "sc://u@%C3%91:1"
    url = URL.build(scheme="sc", authority="u@[::1]:1")
    assert str(url) == "sc://u@[::1]:1"


def test_build_uppercase_scheme() -> None:
    # URL.build() keeps the scheme as given; "HTTP" is still special.
    assert str(URL.build(scheme="HTTP", host="Ñ")) == "HTTP://xn--ida"
    url = URL.build(scheme="HTTP", host="h", query_string="q")
    assert str(url) == "HTTP://h/?q"
    assert url.human_repr() == "HTTP://h/?q="
    assert url.with_host("Ñ").host == "ñ"


def test_build_encoded() -> None:
    assert str(URL.build(scheme="sc", host="Ñ", encoded=True)) == "sc://Ñ"


def test_with_host() -> None:
    url = URL("sc://h/p").with_host("ExÑ")
    assert str(url) == "sc://Ex%C3%91/p"
    assert url == URL("sc://ExÑ/p")
    assert str(URL("sc://h/p").with_host("::1")) == "sc://[::1]/p"
    assert str(URL("sc://h/p", mode="rfc").with_host("ExÑ")) == "sc://xn--ex-0ja/p"


@pytest.mark.parametrize(
    ("url", "scheme", "expected"),
    [
        ("sc://ExAmPlE/", "http", "http://example/"),
        ("sc://u@ñ:1/", "https", "https://u@xn--ida:1/"),
        ("sc://LocalHost/x", "file", "file:///x"),
        ("sc://ExAmPlE/", "other", "other://ExAmPlE/"),
        ("sc://[::1]/", "http", "http://[::1]/"),
    ],
)
def test_with_scheme(url: str, scheme: str, expected: str) -> None:
    assert str(URL(url).with_scheme(scheme)) == expected


@pytest.mark.parametrize("host", ["A{b", "%", "%01"])
def test_with_scheme_invalid_domain(host: str) -> None:
    # As URL(f"http://{host}/") does.
    with pytest.raises(ValueError):
        URL(f"sc://{host}/").with_scheme("http")


def test_with_scheme_encoded() -> None:
    # The URL does not remember that it was built from encoded parts.
    url = URL("sc://A{b/", encoded=True)
    assert str(url) == "sc://A{b/"
    with pytest.raises(ValueError):
        url.with_scheme("http")


def test_mode_change() -> None:
    url = URL("sc://%C3%91/")
    assert str(URL(url, mode="rfc")) == "sc://%C3%91/"
    assert str(URL(URL("sc://Ñ/", mode="rfc"), mode="whatwg")) == "sc://xn--ida/"


@pytest.mark.parametrize(
    ("reference", "whatwg", "rfc"),
    [
        ("x", "sc://%C3%B1/x", "sc://xn--ida/x"),
        ("?x", "sc://%C3%B1?x", "sc://xn--ida?x"),
        ("#x", "sc://%C3%B1#x", "sc://xn--ida#x"),
        ("other://Ñ/", "other://%C3%91/", "other://xn--ida/"),
    ],
)
def test_join(reference: str, whatwg: str, rfc: str) -> None:
    assert str(URL("sc://ñ").join(URL(reference))) == whatwg
    base = URL("sc://ñ", mode="rfc")
    assert str(base.join(URL(reference, mode="rfc"))) == rfc


@pytest.mark.parametrize("mode", [Mode.WHATWG, Mode.RFC])
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sc://h?x=1", "sc://h?x=1"),
        ("sc://h#x", "sc://h#x"),
        ("sc://h?", "sc://h?"),
        ("sc://h#", "sc://h#"),
        ("sc://h?x=1#y", "sc://h?x=1#y"),
        ("sc://h", "sc://h"),
        ("http://h?x=1", "http://h/?x=1"),
        ("http://h#", "http://h/#"),
        ("//h?x=1", "//h/?x=1"),
    ],
)
def test_empty_path(url: str, expected: str, mode: Mode) -> None:
    parsed = URL(url, mode=mode)
    assert str(parsed) == expected
    assert parsed.human_repr() == expected
    assert parsed.raw_path == "/"


def test_empty_path_built() -> None:
    assert str(URL("sc://h").with_query(a="1")) == "sc://h?a=1"
    assert str(URL("sc://h").with_fragment("f")) == "sc://h#f"
    assert str(URL.build(scheme="sc", host="h", query_string="q")) == "sc://h?q"


def test_empty_path_equal_to_slash() -> None:
    # As "sc://h" and "sc://h/" do, the URLs compare equal.
    assert URL("sc://h?x") == URL("sc://h/?x")
    assert hash(URL("sc://h?x")) == hash(URL("sc://h/?x"))
