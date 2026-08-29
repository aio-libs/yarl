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
