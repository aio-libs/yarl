"""WHATWG mode encodes the userinfo with the userinfo percent-encode set.

The WHATWG URL Standard splits the userinfo at the last "@" and keeps "[",
"]" and, for a scheme that is not special, "\\" in it, percent-encoded. RFC
3986 has none of them in its userinfo, so RFC mode rejects them.
"""

import pytest

from yarl import URL

# The cases of the WPT URL corpus, with the base they are joined with.
WPT_CASES = [
    pytest.param(
        "http://&a:foo(b]c@d:2/",
        "http://example.org/foo/bar",
        "http://&a:foo(b%5Dc@d:2/",
        id="bracket-in-password",
    ),
    pytest.param(
        "https://user:pass[\x7f@foo/bar",
        "http://example.org",
        "https://user:pass%5B%7F@foo/bar",
        id="bracket-and-del-in-password",
    ),
    pytest.param(
        "wss:// !\"$%&'()*+,-.;<=>@[]^_`{|}~@host/",
        None,
        "wss://%20!%22$%&'()*+,-.%3B%3C%3D%3E%40%5B%5D%5E_%60%7B%7C%7D~@host/",
        id="special-username",
    ),
    pytest.param(
        "wss://joe: !\"$%&'()*+,-.:;<=>@[]^_`{|}~@host/",
        None,
        "wss://joe:%20!%22$%&'()*+,-.%3A%3B%3C%3D%3E%40%5B%5D%5E_%60%7B%7C%7D~@host/",
        id="special-password",
    ),
    pytest.param(
        "foo:// !\"$%&'()*+,-.;<=>@[\\]^_`{|}~@host/",
        None,
        "foo://%20!%22$%&'()*+,-.%3B%3C%3D%3E%40%5B%5C%5D%5E_%60%7B%7C%7D~@host/",
        id="non-special-username",
    ),
    pytest.param(
        "foo://joe: !\"$%&'()*+,-.:;<=>@[\\]^_`{|}~@host/",
        None,
        "foo://joe:%20!%22$%&'()*+,-.%3A%3B%3C%3D%3E%40%5B%5C%5D%5E_%60%7B%7C%7D~@host/",
        id="non-special-password",
    ),
]


@pytest.mark.parametrize(("url", "base", "expected"), WPT_CASES)
def test_wpt_whatwg_mode(url: str, base: str | None, expected: str) -> None:
    parsed = URL(url) if base is None else URL(base).join(URL(url))
    assert str(parsed) == expected
    assert URL(expected) == parsed


@pytest.mark.parametrize(("url", "base", "expected"), WPT_CASES)
def test_wpt_rfc_mode_rejects(url: str, base: str | None, expected: str) -> None:
    with pytest.raises(ValueError, match="RFC 3986|userinfo cannot contain '@'"):
        URL(url, mode="rfc")


@pytest.mark.parametrize(
    ("url", "expected", "user"),
    [
        ("http://a;b=c@h/", "http://a%3Bb%3Dc@h/", "a;b=c"),
        # "%" is kept as written, also when it starts no percent-encoded
        # octet, and so are the percent-encoded octets.
        ("http://a%b@h/", "http://a%b@h/", "a%b"),
        ("http://a%41%3b@h/", "http://a%41%3b@h/", "aA;"),
        ("http://a@b@h/", "http://a%40b@h/", "a@b"),
        ("http://[a]@h/", "http://%5Ba%5D@h/", "[a]"),
        ("http://[a@h/", "http://%5Ba@h/", "[a"),
        ("http://é@h/", "http://%C3%A9@h/", "é"),
        ("sc://a\\b@h/", "sc://a%5Cb@h/", "a\\b"),
    ],
)
def test_parse_whatwg_mode(url: str, expected: str, user: str) -> None:
    parsed = URL(url)
    assert str(parsed) == expected
    assert parsed.user == user
    assert parsed.host == "h"


@pytest.mark.parametrize(
    "url",
    [
        # A special scheme reads "\\" as "/", so it ends the authority; with
        # encoded=True it is not read, and it is rejected as before.
        "http://a\\b@h/",
        "//a\\b@h/",
        # "\\" is a forbidden host code point.
        "sc://a@h\\b/",
        # Brackets in the host still have to be an IP-literal.
        "http://a[b]@h[::1]/",
        "http://a@[h/",
    ],
)
def test_encoded_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        URL(url, encoded=True)


def test_encoded_keeps_userinfo() -> None:
    url = URL("sc://a[\\]b@h/", encoded=True)
    assert str(url) == "sc://a[\\]b@h/"
    assert url.raw_user == "a[\\]b"
    assert url.host == "h"


def test_rfc_mode_keeps_sub_delims() -> None:
    assert str(URL("http://a;b=c@h/", mode="rfc")) == "http://a;b=c@h/"


def test_build_whatwg_mode() -> None:
    url = URL.build(scheme="http", user="a;b=%", password="c;d", host="h")
    assert str(url) == "http://a%3Bb%3D%25:c%3Bd@h"
    assert url.user == "a;b=%"
    assert url.password == "c;d"
    assert url == URL(str(url))


def test_build_rfc_mode() -> None:
    url = URL.build(scheme="http", user="a;b", password="c=d", host="h", mode="rfc")
    assert str(url) == "http://a;b:c=d@h"


def test_build_authority() -> None:
    url = URL.build(scheme="http", authority="a[b]:c;d@h")
    assert str(url) == "http://a%5Bb%5D:c%3Bd@h"


def test_with_user_and_password() -> None:
    url = URL("http://h/").with_user("a;b").with_password("x=y")
    assert str(url) == "http://a%3Bb:x%3Dy@h/"
    rfc_url = URL("http://h/", mode="rfc").with_user("a;b").with_password("x=y")
    assert str(rfc_url) == "http://a;b:x=y@h/"


def test_mode_change() -> None:
    rfc_url = URL("http://a;b:c=d@h/", mode="rfc")
    whatwg_url = URL(rfc_url, mode="whatwg")
    assert str(whatwg_url) == "http://a%3Bb:c%3Dd@h/"
    assert whatwg_url == URL("http://a;b:c=d@h/")
    assert whatwg_url.user == "a;b"


def test_join_rfc_reference() -> None:
    joined = URL("http://x/").join(URL("//a;b@h/p", mode="rfc"))
    assert str(joined) == "http://a%3Bb@h/p"
