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
