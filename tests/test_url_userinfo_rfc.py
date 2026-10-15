"""RFC 3986 mode keeps an empty userinfo with its "@"; WHATWG mode drops it."""

import pickle

import pytest

from yarl import URL


@pytest.mark.parametrize(
    ("url", "whatwg"),
    [
        ("http://@www.example.com", "http://www.example.com"),
        ("http://@pple.com", "http://pple.com"),
        ("http://@h/p?q#f", "http://h/p?q#f"),
        ("http://@h:8080/", "http://h:8080/"),
        ("http://@[::1]/", "http://[::1]/"),
        ("sc://@h", "sc://h"),
        ("sc://@h/x", "sc://h/x"),
        # An empty username before an empty password, see also
        # test_url_userinfo_whatwg.py.
        ("http://:@h/", "http://h/"),
        ("http://:p@h/", "http://:p@h/"),
    ],
)
def test_parse(url: str, whatwg: str) -> None:
    whatwg_url = URL(url)
    assert str(whatwg_url) == whatwg
    assert URL(whatwg) == whatwg_url
    assert hash(URL(whatwg)) == hash(whatwg_url)
    rfc_url = URL(url, mode="rfc")
    assert str(rfc_url) == url
    assert URL(str(rfc_url), mode="rfc") == rfc_url
    assert hash(URL(str(rfc_url), mode="rfc")) == hash(rfc_url)


def test_default_port() -> None:
    # The default port is dropped when written out, the userinfo is not.
    assert str(URL("http://@h:80/", mode="rfc")) == "http://@h/"
    assert str(URL("http://@h:80/")) == "http://h/"


def test_empty_host() -> None:
    # RFC 3986 allows an empty host after an empty userinfo.
    url = URL("sc://@/", mode="rfc")
    assert str(url) == "sc://@/"
    assert url.raw_authority == url.authority == "@"
    assert url.raw_user == ""
    assert url.raw_host is None
    with pytest.raises(ValueError, match="host is required"):
        URL("sc://@/")


@pytest.mark.parametrize(
    ("url", "password"),
    [
        ("http://@h/", None),
        ("http://:@h/", ""),
        ("http://:p@h/", "p"),
    ],
)
def test_parts(url: str, password: str | None) -> None:
    # The username is "" in RFC mode, None means there is no userinfo.
    rfc_url = URL(url, mode="rfc")
    assert rfc_url.raw_user == rfc_url.user == ""
    assert rfc_url.raw_password == rfc_url.password == password
    # A URL that is not parsed splits its authority, see _cache_netloc().
    built = URL.build(scheme="http", authority=rfc_url.raw_authority, mode="rfc")
    assert built.raw_user == built.user == ""
    assert built.raw_password == password
    whatwg_url = URL(url)
    assert whatwg_url.raw_user is whatwg_url.user is None
    assert whatwg_url.raw_password == (password or None)


def test_no_userinfo() -> None:
    url = URL("http://h/", mode="rfc")
    assert url.raw_user is None
    assert url.user is None
    assert url.raw_password is None


def test_authority() -> None:
    url = URL("http://@h:8080/", mode="rfc")
    assert url.raw_authority == "@h:8080"
    assert url.authority == "@h:8080"
    assert URL("http://@h:8080/").raw_authority == "h:8080"


def test_equality() -> None:
    # Different URIs under RFC 3986, also after normalization.
    with_userinfo = URL("http://@h/", mode="rfc")
    without = URL("http://h/", mode="rfc")
    assert with_userinfo != without
    assert hash(with_userinfo) != hash(without)
    assert URL("http://@h/") == URL("http://h/")


def test_human_repr() -> None:
    assert URL("http://@h/p", mode="rfc").human_repr() == "http://@h/p"
    assert URL("http://@h/p").human_repr() == "http://h/p"


def test_origin() -> None:
    assert str(URL("http://@h/p", mode="rfc").origin()) == "http://h"


def test_encoded_kept() -> None:
    # encoded=True takes the input as it is, in both modes.
    url = URL("http://@h/", encoded=True)
    assert str(url) == "http://@h/"
    assert url.raw_user is None
    rfc_url = URL("http://@h/", encoded=True, mode="rfc")
    assert str(rfc_url) == "http://@h/"
    assert rfc_url.raw_user == ""


@pytest.mark.parametrize(
    ("user", "password", "whatwg", "rfc"),
    [
        ("", None, "http://h/p", "http://@h/p"),
        ("", "", "http://h/p", "http://:@h/p"),
        ("", "p", "http://:p@h/p", "http://:p@h/p"),
        (None, None, "http://h/p", "http://h/p"),
    ],
)
def test_build(user: str | None, password: str | None, whatwg: str, rfc: str) -> None:
    url = URL.build(scheme="http", user=user, password=password, host="h", path="/p")
    assert str(url) == whatwg
    assert url == URL(whatwg)
    rfc_url = URL.build(
        scheme="http", user=user, password=password, host="h", path="/p", mode="rfc"
    )
    assert str(rfc_url) == rfc
    assert rfc_url == URL(rfc, mode="rfc")


@pytest.mark.parametrize(
    ("authority", "whatwg", "rfc"),
    [
        ("@h", "sc://h/p", "sc://@h/p"),
        ("@h:1", "sc://h:1/p", "sc://@h:1/p"),
        (":@h", "sc://h/p", "sc://:@h/p"),
    ],
)
def test_build_authority(authority: str, whatwg: str, rfc: str) -> None:
    url = URL.build(scheme="sc", authority=authority, path="/p")
    assert str(url) == whatwg
    assert url == URL(whatwg)
    rfc_url = URL.build(scheme="sc", authority=authority, path="/p", mode="rfc")
    assert str(rfc_url) == rfc
    assert rfc_url == URL(rfc, mode="rfc")


@pytest.mark.parametrize(
    ("user", "password", "whatwg", "rfc"),
    [
        ("", None, "http://h", "http://@h"),
        ("", "", "http://:@h", "http://:@h"),
        ("", "p", "http://:p@h", "http://:p@h"),
    ],
)
def test_build_encoded(user: str, password: str | None, whatwg: str, rfc: str) -> None:
    # As before, WHATWG mode drops an empty user, but keeps an empty password
    # as it is given.
    kwargs = {"scheme": "http", "user": user, "password": password, "host": "h"}
    assert str(URL.build(**kwargs, encoded=True)) == whatwg  # type: ignore[arg-type]
    rfc_url = URL.build(**kwargs, encoded=True, mode="rfc")  # type: ignore[arg-type]
    assert str(rfc_url) == rfc


@pytest.mark.parametrize(
    ("url", "whatwg", "rfc"),
    [
        ("http://h/", "http://h/", "http://@h/"),
        ("http://a@h/", "http://h/", "http://@h/"),
        ("http://a:p@h/", "http://:p@h/", "http://:p@h/"),
    ],
)
def test_with_user_empty(url: str, whatwg: str, rfc: str) -> None:
    whatwg_url = URL(url).with_user("")
    assert str(whatwg_url) == whatwg
    assert whatwg_url.raw_user is None
    rfc_url = URL(url, mode="rfc").with_user("")
    assert str(rfc_url) == rfc
    assert rfc_url.raw_user == ""


def test_with_user_none() -> None:
    assert str(URL("http://@h/", mode="rfc").with_user(None)) == "http://h/"
    assert str(URL("http://:p@h/", mode="rfc").with_user(None)) == "http://h/"


@pytest.mark.parametrize("user", [0, b"", 1, b"a"])
def test_with_user_invalid_type(user: object) -> None:
    with pytest.raises(TypeError, match="Invalid user type"):
        URL("http://h/", mode="rfc").with_user(user)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("url", "password", "rfc"),
    [
        ("http://@h/", "p", "http://:p@h/"),
        ("http://@h/", "", "http://:@h/"),
        ("http://:p@h/", None, "http://@h/"),
        ("http://@h/", None, "http://@h/"),
    ],
)
def test_with_password(url: str, password: str | None, rfc: str) -> None:
    # The empty username stays when the password changes.
    rfc_url = URL(url, mode="rfc").with_password(password)
    assert str(rfc_url) == rfc
    assert rfc_url.raw_user == ""


def test_with_host_and_port() -> None:
    url = URL("http://@h/", mode="rfc")
    assert str(url.with_host("x")) == "http://@x/"
    assert str(url.with_port(81)) == "http://@h:81/"
    assert str(url.with_port(81).with_port(None)) == "http://@h/"
    assert url.with_host("x").raw_user == ""


@pytest.mark.parametrize("scheme", ["https", "sc", "file"])
def test_with_scheme(scheme: str) -> None:
    rfc_url = URL("http://@h/", mode="rfc").with_scheme(scheme)
    assert str(rfc_url) == f"{scheme}://@h/"
    assert rfc_url.raw_user == ""


@pytest.mark.parametrize(
    ("url", "whatwg"),
    [
        ("http://@h/", "http://h/"),
        ("http://@h:1/", "http://h:1/"),
        ("sc://@h/", "sc://h/"),
        ("http://:@h/", "http://h/"),
        ("http://:p@h/", "http://:p@h/"),
    ],
)
def test_mode_change(url: str, whatwg: str) -> None:
    rfc_url = URL(url, mode="rfc")
    whatwg_url = URL(rfc_url, mode="whatwg")
    assert str(whatwg_url) == whatwg
    assert whatwg_url == URL(whatwg)
    assert whatwg_url.raw_user is None
    # A WHATWG URL has no empty userinfo to bring back.
    assert str(URL(whatwg_url, mode="rfc")) == whatwg


@pytest.mark.parametrize(
    ("base", "ref", "whatwg", "rfc"),
    [
        ("http://u:p@h/a", "//@x", "http://x", "http://@x"),
        ("http://u:p@h/a", "//@x/p?q", "http://x/p?q", "http://@x/p?q"),
        ("sc://u@h/a", "//@x", "sc://x", "sc://@x"),
        ("sc://u@h/a", "sc://@x/p", "sc://x/p", "sc://@x/p"),
        # The base keeps its empty userinfo when the reference has none.
        ("http://@h/a", "b", "http://h/b", "http://@h/b"),
        ("http://@h/a", "//x", "http://x", "http://x"),
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
    assert str(base.join(URL("//@x/p", mode="rfc"))) == "http://x/p"
    assert str(base.join(URL("sc://@x", mode="rfc"))) == "sc://x"


def test_pickle() -> None:
    url = URL("http://@h/", mode="rfc")
    loaded = pickle.loads(pickle.dumps(url))
    assert loaded == url
    assert str(loaded) == "http://@h/"
    assert loaded.raw_user == ""
