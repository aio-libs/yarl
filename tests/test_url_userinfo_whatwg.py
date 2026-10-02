"""WHATWG mode drops an empty password, and an empty userinfo with its "@"."""

import pickle

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        ("http://a:@h/", "http://a@h/", "http://a:@h/"),
        ("http://:@h/", "http://h/", "http://:@h/"),
        ("https://test:@test", "https://test@test", "https://test:@test"),
        ("https://:@test", "https://test", "https://:@test"),
        ("non-special://test:@test/x", "non-special://test@test/x", None),
        ("non-special://:@test/x", "non-special://test/x", None),
        ("http://a:@h:8080/p?q#f", "http://a@h:8080/p?q#f", None),
        ("http://a:@[::1]/", "http://a@[::1]/", None),
        # A special URL without "//" reads the authority in WHATWG mode.
        (
            "http:a:@www.example.com",
            "http://a@www.example.com",
            "http:a:@www.example.com",
        ),
        (
            "http:/a:@www.example.com",
            "http://a@www.example.com",
            "http:/a:@www.example.com",
        ),
        # A password that is not empty is kept, also with an empty username.
        ("http://:p@h/", "http://:p@h/", "http://:p@h/"),
        ("http://a:p@h/", "http://a:p@h/", "http://a:p@h/"),
        ("http://a@h/", "http://a@h/", "http://a@h/"),
        # An empty userinfo drops "@" in WHATWG mode; RFC 3986 keeps it.
        ("http://@h/", "http://h/", "http://@h/"),
    ],
)
def test_parse(url: str, whatwg: str, rfc: str | None) -> None:
    whatwg_url = URL(url)
    assert str(whatwg_url) == whatwg
    assert URL(whatwg) == whatwg_url
    assert hash(URL(whatwg)) == hash(whatwg_url)
    rfc_url = URL(url, mode="rfc")
    assert str(rfc_url) == (url if rfc is None else rfc)
    assert URL(str(rfc_url), mode="rfc") == rfc_url


@pytest.mark.parametrize(
    ("url", "user", "password"),
    [
        ("http://a:@h/", "a", ""),
        ("http://:@h/", None, ""),
        ("http://:p@h/", None, "p"),
    ],
)
def test_parts(url: str, user: str | None, password: str) -> None:
    # WHATWG mode has no empty password, as yarl has no empty username: both
    # are None. RFC mode keeps the empty username and the empty password.
    whatwg_url = URL(url)
    assert whatwg_url.raw_user == whatwg_url.user == user
    assert whatwg_url.raw_password == whatwg_url.password == (password or None)
    rfc_url = URL(url, mode="rfc")
    assert rfc_url.raw_user == rfc_url.user == (user or "")
    assert rfc_url.raw_password == rfc_url.password == password


def test_authority() -> None:
    url = URL("http://a:@h:8080/")
    assert url.raw_authority == "a@h:8080"
    assert url.authority == "a@h:8080"
    assert URL("http://a:@h:8080/", mode="rfc").raw_authority == "a:@h:8080"


def test_encoded_kept() -> None:
    # Like the file host rules, encoded=True takes the input as it is.
    url = URL("http://a:@h/", encoded=True)
    assert str(url) == "http://a:@h/"
    assert url.raw_password == ""
    assert str(url.with_host("x")) == "http://a:@x/"
    assert str(url.with_port(81)) == "http://a:@h:81/"


@pytest.mark.parametrize(
    ("user", "password", "whatwg", "rfc"),
    [
        ("a", "", "http://a@h/p", "http://a:@h/p"),
        ("", "", "http://h/p", "http://:@h/p"),
        (None, "", "http://h/p", "http://:@h/p"),
        ("", "p", "http://:p@h/p", "http://:p@h/p"),
        ("a", "p", "http://a:p@h/p", "http://a:p@h/p"),
    ],
)
def test_build(user: str | None, password: str, whatwg: str, rfc: str) -> None:
    url = URL.build(scheme="http", user=user, password=password, host="h", path="/p")
    assert str(url) == whatwg
    assert url == URL(whatwg)
    rfc_url = URL.build(
        scheme="http", user=user, password=password, host="h", path="/p", mode="rfc"
    )
    assert str(rfc_url) == rfc


@pytest.mark.parametrize(
    ("authority", "whatwg", "rfc"),
    [
        ("a:@h", "sc://a@h/p", "sc://a:@h/p"),
        (":@h", "sc://h/p", "sc://:@h/p"),
        (":@h:1", "sc://h:1/p", "sc://:@h:1/p"),
        (":p@h", "sc://:p@h/p", "sc://:p@h/p"),
    ],
)
def test_build_authority(authority: str, whatwg: str, rfc: str) -> None:
    url = URL.build(scheme="sc", authority=authority, path="/p")
    assert str(url) == whatwg
    assert url == URL(whatwg)
    rfc_url = URL.build(scheme="sc", authority=authority, path="/p", mode="rfc")
    assert str(rfc_url) == rfc


def test_build_encoded_kept() -> None:
    url = URL.build(scheme="http", user="a", password="", host="h", encoded=True)
    assert str(url) == "http://a:@h"
    url = URL.build(scheme="http", authority="a:@h", encoded=True)
    assert str(url) == "http://a:@h"


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        ("http://a:p@h/", "http://a@h/", "http://a:@h/"),
        ("http://:p@h/", "http://h/", "http://:@h/"),
        ("http://h/", "http://h/", "http://:@h/"),
    ],
)
def test_with_password_empty(url: str, whatwg: str, rfc: str) -> None:
    whatwg_url = URL(url).with_password("")
    assert str(whatwg_url) == whatwg
    assert whatwg_url.raw_password is None
    assert str(URL(url, mode="rfc").with_password("")) == rfc


def test_with_password() -> None:
    assert str(URL("http://a@h/").with_password("p q")) == "http://a:p%20q@h/"
    assert str(URL("http://a:p@h/").with_password(None)) == "http://a@h/"


@pytest.mark.parametrize(
    ("user", "whatwg", "rfc"),
    [
        ("b", "http://b@h/", "http://b:@h/"),
        ("", "http://h/", "http://:@h/"),
        (None, "http://h/", "http://h/"),
    ],
)
def test_with_user(user: str | None, whatwg: str, rfc: str) -> None:
    assert str(URL("http://a:@h/").with_user(user)) == whatwg
    assert str(URL("http://a:@h/", mode="rfc").with_user(user)) == rfc


def test_with_host_and_port() -> None:
    url = URL("http://a:@h/")
    assert str(url.with_host("x")) == "http://a@x/"
    assert str(url.with_port(81)) == "http://a@h:81/"
    rfc_url = URL("http://a:@h/", mode="rfc")
    assert str(rfc_url.with_host("x")) == "http://a:@x/"
    assert str(rfc_url.with_port(81)) == "http://a:@h:81/"


@pytest.mark.parametrize("scheme", ["https", "sc"])
def test_with_scheme(scheme: str) -> None:
    assert str(URL("http://a:@h/").with_scheme(scheme)) == f"{scheme}://a@h/"
    rfc_url = URL("http://a:@h/", mode="rfc")
    assert str(rfc_url.with_scheme(scheme)) == f"{scheme}://a:@h/"


@pytest.mark.parametrize(
    ("url", "whatwg"),
    [
        ("http://a:@h/", "http://a@h/"),
        ("http://:@h/", "http://h/"),
        ("sc://a:@h/", "sc://a@h/"),
        ("sc://:@h:1/", "sc://h:1/"),
        ("http://a:p@h/", "http://a:p@h/"),
        ("http://a@h/", "http://a@h/"),
    ],
)
def test_mode_change(url: str, whatwg: str) -> None:
    rfc_url = URL(url, mode="rfc")
    whatwg_url = URL(rfc_url, mode="whatwg")
    assert str(whatwg_url) == whatwg
    assert whatwg_url == URL(str(whatwg_url))
    # Going back to RFC mode does not bring the password back.
    assert str(URL(whatwg_url, mode="rfc")) == str(whatwg_url)


def test_mode_change_password_with_colon() -> None:
    # The password "p:" is not empty, though the authority has ":@" in it.
    rfc_url = URL("sc://u:p:@h/", encoded=True, mode="rfc")
    whatwg_url = URL(rfc_url, mode="whatwg")
    assert str(whatwg_url) == "sc://u:p:@h/"
    assert whatwg_url.raw_password == "p:"


@pytest.mark.parametrize(
    ("base", "ref", "whatwg", "rfc"),
    [
        ("http://u:p@h/a", "//:@x", "http://x", "http://:@x"),
        ("http://u:p@h/a", "//v:@x/p", "http://v@x/p", "http://v:@x/p"),
        ("http://u:p@h/a", "//@x", "http://x", "http://@x"),
        ("http://u:p@h/a", "//:q@x", "http://:q@x", "http://:q@x"),
        ("sc://u@h/a", "//:@x", "sc://x", "sc://:@x"),
        ("sc://u@h/a", "//v:@x", "sc://v@x", "sc://v:@x"),
        ("sc://u@h/a", "http://v:@x", "http://v@x", "http://v:@x"),
        ("sc://u@h/a", "http:v:@x", "http://v@x", "http:v:@x"),
        # Against a base with the same special scheme, "http:v:@x" is the
        # path "v:@x" in WHATWG mode, and RFC 3986 takes it as it is.
        ("http://u:p@h/a", "http:v:@x", "http://u:p@h/v:@x", "http:v:@x"),
        # The base keeps its userinfo when the reference has no authority.
        ("http://u:p@h/a", "b", "http://u:p@h/b", "http://u:p@h/b"),
    ],
)
def test_join(base: str, ref: str, whatwg: str, rfc: str) -> None:
    joined = URL(base).join(URL(ref))
    assert str(joined) == whatwg
    rfc_joined = URL(base, mode="rfc").join(URL(ref, mode="rfc"))
    assert str(rfc_joined) == rfc


def test_join_rfc_reference() -> None:
    # The result follows the mode of the base.
    base = URL("http://h/a")
    assert str(base.join(URL("//v:@x/p", mode="rfc"))) == "http://v@x/p"
    assert str(base.join(URL("sc://v:@x", mode="rfc"))) == "sc://v@x"


def test_pickle() -> None:
    url = URL("http://a:@h/")
    assert pickle.loads(pickle.dumps(url)) == url
    assert str(pickle.loads(pickle.dumps(url))) == "http://a@h/"
