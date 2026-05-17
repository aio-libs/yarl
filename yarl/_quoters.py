"""Quoting and unquoting utilities for URL parts."""

import re
from functools import lru_cache
from urllib.parse import quote

from ._quoting import _Quoter, _Unquoter

QUOTER = _Quoter(requote=False)
REQUOTER = _Quoter()
PATH_QUOTER = _Quoter(safe="@:", protected="/+", requote=False)
PATH_REQUOTER = _Quoter(safe="@:", protected="/+")
QUERY_QUOTER = _Quoter(safe="?/:@", protected="=+&;", qs=True, requote=False)
QUERY_REQUOTER = _Quoter(safe="?", protected="=+&;$'()*,:/@", qs=True)
QUERY_PART_QUOTER = _Quoter(safe="?", qs=True, requote=False, unsafe="$'()*,")
FRAGMENT_QUOTER = _Quoter(safe="?/:@", requote=False)
FRAGMENT_REQUOTER = _Quoter(safe="?/:@")

UNQUOTER = _Unquoter()
PATH_UNQUOTER = _Unquoter(unsafe="+")
PATH_SAFE_UNQUOTER = _Unquoter(ignore="/%", unsafe="+")
QS_UNQUOTER = _Unquoter(qs=True)
UNQUOTER_PLUS = _Unquoter(plus=True)  # to match urllib.parse.unquote_plus


@lru_cache(maxsize=16)
def _human_quote_table(unsafe: str) -> dict[int, str]:
    return {ord(c): f"%{ord(c):02X}" for c in "%" + unsafe}


@lru_cache(maxsize=16)
def _human_quote_re(unsafe: str) -> re.Pattern[str]:
    return re.compile(f"[{re.escape('%' + unsafe)}]")


def human_quote(s: str | None, unsafe: str) -> str | None:
    if not s:
        return s
    if s.isalnum() or (
        "/" not in unsafe and (s == "/" or s.startswith("/") and s[1:].isalnum())
    ):
        return s
    if _human_quote_re(unsafe).search(s):
        s = s.translate(_human_quote_table(unsafe))
    if s.isprintable():
        return s
    return "".join(c if c.isprintable() else quote(c) for c in s)
