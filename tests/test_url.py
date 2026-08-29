import platform
import sys
from enum import Enum
from urllib.parse import SplitResult, quote, unquote

import pytest

from yarl import URL
from yarl._url import _DEFAULT_IGNORABLE_RE, _idna_encode

_WHATWG_C0_CONTROL_OR_SPACE = (
    "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10"
    "\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f "
)
_VERTICAL_COLON = "\ufe13"  # normalizes to ":"
_FULL_WITH_NUMBER_SIGN = "\uff03"  # normalizes to "#"
_ACCOUNT_OF = "\u2100"  # normalizes to "a/c"
_FULLWIDTH_PERCENT = "\uff05"  # normalizes to "%"
_SMALL_PERCENT = "\ufe6a"  # normalizes to "%"


def test_inheritance() -> None:
    with pytest.raises(TypeError) as ctx:

        class MyURL(URL):
            pass

    assert (
        "Inheriting a class "
        "<class 'test_url.test_inheritance.<locals>.MyURL'> "
        "from URL is forbidden" == str(ctx.value)
    )


def test_str_subclass() -> None:
    class S(str):
        pass

    assert str(URL(S("http://example.com"))) == "http://example.com"


def test_is() -> None:
    u1 = URL("http://example.com")
    u2 = URL(u1)
    assert u1 is u2


def test_bool() -> None:
    assert URL("http://example.com")
    assert not URL()
    assert not URL("")


def test_absolute_url_without_host() -> None:
    with pytest.raises(ValueError):
        URL("http://:8080/")


def test_url_is_not_str() -> None:
    url = URL("http://example.com")
    assert not isinstance(url, str)  # type: ignore[unreachable]


def test_str() -> None:
    url = URL("http://example.com:8888/path/to?a=1&b=2")
    assert str(url) == "http://example.com:8888/path/to?a=1&b=2"


def test_repr() -> None:
    url = URL("http://example.com")
    assert "URL('http://example.com')" == repr(url)


def test_origin() -> None:
    url = URL("http://user:password@example.com:8888/path/to?a=1&b=2")
    assert URL("http://example.com:8888") == url.origin()


def test_origin_is_equal_to_self() -> None:
    url = URL("http://example.com:8888")
    assert url.origin() == url


def test_origin_with_no_auth() -> None:
    url = URL("http://example.com:8888/path/to?a=1&b=2")
    assert URL("http://example.com:8888") == url.origin()


def test_origin_nonascii() -> None:
    url = URL("http://user:password@оун-упа.укр:8888/path/to?a=1&b=2")
    assert str(url.origin()) == "http://xn----8sb1bdhvc.xn--j1amh:8888"


def test_origin_ipv6() -> None:
    url = URL("http://user:password@[::1]:8888/path/to?a=1&b=2")
    assert str(url.origin()) == "http://[::1]:8888"


def test_origin_not_absolute_url() -> None:
    url = URL("/path/to?a=1&b=2")
    with pytest.raises(ValueError):
        url.origin()


def test_origin_no_scheme() -> None:
    url = URL("//user:password@example.com:8888/path/to?a=1&b=2")
    with pytest.raises(ValueError):
        url.origin()


def test_drop_dots() -> None:
    u = URL("http://example.com/path/../to")
    assert str(u) == "http://example.com/to"


def test_abs_cmp() -> None:
    assert URL("http://example.com:8888") == URL("http://example.com:8888")
    assert URL("http://example.com:8888/") == URL("http://example.com:8888/")
    assert URL("http://example.com:8888/") == URL("http://example.com:8888")
    assert URL("http://example.com:8888") == URL("http://example.com:8888/")


def test_abs_hash() -> None:
    url = URL("http://example.com:8888")
    url_trailing = URL("http://example.com:8888/")
    assert hash(url) == hash(url_trailing)


# properties


def test_scheme() -> None:
    url = URL("http://example.com")
    assert "http" == url.scheme


def test_raw_user() -> None:
    url = URL("http://user@example.com")
    assert "user" == url.raw_user
    assert url.raw_user == SplitResult(*url._val).username


def test_raw_user_non_ascii() -> None:
    url = URL("http://бажан@example.com")
    assert "%D0%B1%D0%B0%D0%B6%D0%B0%D0%BD" == url.raw_user
    assert url.raw_user == SplitResult(*url._val).username


def test_no_user() -> None:
    url = URL("http://example.com")
    assert url.user is None


def test_user_non_ascii() -> None:
    url = URL("http://бажан@example.com")
    assert "бажан" == url.user


def test_raw_password() -> None:
    url = URL("http://user:password@example.com")
    assert "password" == url.raw_password
    assert url.raw_password == SplitResult(*url._val).password


def test_raw_password_non_ascii() -> None:
    url = URL("http://user:пароль@example.com")
    assert "%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C" == url.raw_password
    assert url.raw_password == SplitResult(*url._val).password


def test_password_non_ascii() -> None:
    url = URL("http://user:пароль@example.com")
    assert "пароль" == url.password


def test_password_without_user() -> None:
    url = URL("http://:password@example.com")
    assert url.user is None
    assert "password" == url.password


def test_empty_password_without_user() -> None:
    url = URL("http://:@example.com")
    assert url.user is None
    assert url.password == ""
    assert url.raw_password == ""
    assert url.raw_password == SplitResult(*url._val).password


def test_user_empty_password() -> None:
    url = URL("http://user:@example.com")
    assert "user" == url.user
    assert "" == url.password


def test_raw_host() -> None:
    url = URL("http://example.com")
    assert "example.com" == url.raw_host
    assert url.raw_host == SplitResult(*url._val).hostname


@pytest.mark.parametrize(
    ("host"),
    [
        ("example.com"),
        ("[::1]"),
        ("xn--gnter-4ya.com"),
    ],
)
def test_host_subcomponent(host: str) -> None:
    url = URL(f"http://{host}")
    assert url.host_subcomponent == host


@pytest.mark.parametrize(
    ("input", "result"),
    [
        ("/", None),
        ("http://example.com", "example.com"),
        ("http://[::1]", "[::1]"),
        ("http://xn--gnter-4ya.com", "xn--gnter-4ya.com"),
        ("http://example.com.", "example.com"),
        ("https://example.com.", "example.com"),
        ("http://example.com:80", "example.com"),
        ("http://example.com:8080", "example.com:8080"),
        ("http://[::1]:8080", "[::1]:8080"),
    ],
)
def test_host_port_subcomponent(input: str, result: str) -> None:
    url = URL(input)
    assert url.host_port_subcomponent == result


def test_host_subcomponent_return_idna_encoded_host() -> None:
    url = URL("http://оун-упа.укр")
    assert url.host_subcomponent == "xn----8sb1bdhvc.xn--j1amh"


def test_invalid_idna_hyphen_encoding() -> None:
    url = URL("http://x-----xn1agdj.tld")
    assert url.host == "x-----xn1agdj.tld"


def test_invalid_idna_a_label_encoding() -> None:
    url = URL("http://xn--d.tld")
    assert url.raw_host == "xn--d.tld"


def test_raw_host_non_ascii() -> None:
    url = URL("http://оун-упа.укр")
    assert "xn----8sb1bdhvc.xn--j1amh" == url.raw_host
    assert url.raw_host == SplitResult(*url._val).hostname


def test_host_non_ascii() -> None:
    url = URL("http://оун-упа.укр")
    assert "оун-упа.укр" == url.host


def test_localhost() -> None:
    url = URL("http://[::1]")
    assert "::1" == url.host


def test_host_with_underscore() -> None:
    url = URL("http://abc_def.com")
    assert "abc_def.com" == url.host


def test_raw_host_when_port_is_specified() -> None:
    url = URL("http://example.com:8888")
    assert "example.com" == url.raw_host
    assert url.raw_host == SplitResult(*url._val).hostname


def test_raw_host_from_str_with_ipv4() -> None:
    url = URL("http://127.0.0.1:80")
    assert url.raw_host == "127.0.0.1"
    assert url.raw_host == SplitResult(*url._val).hostname


def test_raw_host_from_str_with_ipv6() -> None:
    url = URL("http://[::1]:80")
    assert url.raw_host == "::1"
    assert url.raw_host == SplitResult(*url._val).hostname


def test_authority_full() -> None:
    url = URL("http://user:passwd@host.com:8080/path")
    assert url.raw_authority == "user:passwd@host.com:8080"
    assert url.authority == "user:passwd@host.com:8080"


def test_authority_short() -> None:
    url = URL("http://host.com/path")
    assert url.raw_authority == "host.com"


def test_authority_full_nonasci() -> None:
    url = URL("http://степан:пароль@слава.укр:8080/path")
    assert url.raw_authority == (
        "%D1%81%D1%82%D0%B5%D0%BF%D0%B0%D0%BD:"
        "%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C@"
        "xn--80aaf8a3a.xn--j1amh:8080"
    )
    assert url.authority == "степан:пароль@слава.укр:8080"


def test_authority_unknown_scheme() -> None:
    v = "scheme://user:password@example.com:43/path/to?a=1&b=2"
    url = URL(v)
    assert str(url) == v


def test_lowercase() -> None:
    url = URL("http://gitHUB.com")
    assert url.raw_host == "github.com"
    assert url.host == url.raw_host
    assert url.raw_host == SplitResult(*url._val).hostname


def test_lowercase_nonascii() -> None:
    url = URL("http://Слава.Укр")
    assert url.raw_host == "xn--80aaf8a3a.xn--j1amh"
    assert url.raw_host == SplitResult(*url._val).hostname
    assert url.host == "слава.укр"


def test_compressed_ipv6() -> None:
    url = URL("http://[1DEC:0:0:0::1]")
    assert url.raw_host == "1dec::1"
    assert url.host == url.raw_host
    assert url.raw_host == SplitResult(*url._val).hostname


def test_ipv6_missing_left_bracket() -> None:
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL("http://[1dec:0:0:0::1/")


def test_ipv6_missing_right_bracket() -> None:
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL("http://[1dec:0:0:0::1/")


@pytest.mark.parametrize(
    "url",
    (
        "http://[]/",
        "http://[1]/",
        "http://[127.0.0.1]/",
    ),
    ids=(
        "empty-IPv6-like-URL",
        "no-colons-in-IPv6",
        "IPv4-inside-brackets",
    ),
)
def test_ipv6_invalid_url(url: str) -> None:
    with pytest.raises(
        ValueError, match="The IPv6 content between brackets is not valid"
    ):
        URL(url)


def test_ipv6_brackets_in_reversed_order() -> None:
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL("http://]1dec:0:0:0::1[/")


@pytest.mark.parametrize(
    "url",
    (
        "http://127.0.0.1[aa::ff]",
        "http://127.0.0.1[aa::ff]/",
        "http://127.0.0.1[aa::ff]:8080/",
        "http://user@127.0.0.1[aa::ff]/",
        "http://example.com[::1]/",
    ),
    ids=(
        "ipv4-before-bracket",
        "ipv4-before-bracket-with-path",
        "ipv4-before-bracket-with-port",
        "userinfo-ipv4-before-bracket",
        "hostname-before-bracket",
    ),
)
def test_host_with_text_before_bracket_is_invalid(url: str) -> None:
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL(url)


@pytest.mark.parametrize(
    "url",
    (
        "http://[::1]allowed.example:1/",
        "http://[::1]evil.com/",
        "http://[::1]evil.com:8080/",
        "http://user@[::1]evil.com:1/",
        "http://[::1]evil/",
        "http://[::1].:80/",
    ),
    ids=(
        "suffix-with-port",
        "suffix-no-port",
        "suffix-with-explicit-port",
        "userinfo-suffix-with-port",
        "short-suffix-no-port",
        "dot-suffix-with-port",
    ),
)
def test_host_with_text_after_bracket_is_invalid(url: str) -> None:
    """Text after the closing bracket of an IP-literal is invalid.

    Per RFC 3986 §3.2.2, after the closing ']' of an IP-literal only
    ':' <port> or end-of-authority is valid. Previously yarl silently
    dropped the suffix (e.g. '[::1]allowed.example:1' -> '[::1]:1'),
    changing the effective host identity.
    """
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL(url)


def test_build_authority_with_text_after_bracket_is_invalid() -> None:
    """URL.build(authority=...) must also reject text after ']'."""
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL.build(scheme="http", authority="[::1]allowed.example:1", path="/")


def test_ipfuture_brackets_not_allowed() -> None:
    with pytest.raises(ValueError, match="IPvFuture address is invalid"):
        URL("http://[v10]/")


@pytest.mark.parametrize(
    "url",
    (
        "http://[:localhost[]].google:80",
        "http://[:localhost[]].google",
        "http://[:attacker.com[]]:80",
        "http://[:evil.com[]].bank.com:443",
        "http://[:127.0.0.1[]]:80",
        "http://[v1.:attacker[]].bank.com:80",
    ),
    ids=(
        "host-confusion-with-port",
        "host-confusion-without-port",
        "attacker-host-injection",
        "domain-allowlist-bypass",
        "private-ip-injection",
        "ipvfuture-bracket-abuse",
    ),
)
def test_malformed_bracketed_host_rejected(url: str) -> None:
    """Reject URLs with multiple brackets to prevent host confusion (SSRF)."""
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL(url)


def test_malformed_bracketed_host_in_authority() -> None:
    """Reject malformed brackets via URL.build(authority=...) path."""
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL.build(scheme="http", authority="[:localhost[]].google:80")


def test_userinfo_with_bracketed_host_is_valid() -> None:
    """Ensure the multi-bracket check still accepts userinfo + IP-literal host."""
    url = URL("http://user:pass@[::1]:8080/")
    assert url.user == "user"
    assert url.password == "pass"
    assert url.raw_host == "::1"
    assert url.port == 8080


@pytest.mark.parametrize(
    "url",
    (
        "http://[::1]@",
        "//[]@",
        "//a[b]c@",
    ),
    ids=(
        "ipv6-literal-followed-by-empty-host",
        "empty-brackets-followed-by-empty-host",
        "text-around-brackets-followed-by-empty-host",
    ),
)
def test_bracketed_host_followed_by_empty_host_is_invalid(url: str) -> None:
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        URL(url)


def test_ipv4_zone() -> None:
    # I'm unsure if it is correct.
    url = URL("http://1.2.3.4%тест%42:123")
    assert url.raw_host == "1.2.3.4%тест%42"
    assert url.host == url.raw_host
    assert url.raw_host == SplitResult(*url._val).hostname
