"""Quoting and unquoting utilities for URL parts."""

from urllib.parse import quote

from ._quoting import _Quoter, _Unquoter

QUOTER = _Quoter(requote=False)
REQUOTER = _Quoter()
PATH_QUOTER = _Quoter(safe="@:", protected="/+", requote=False)
PATH_REQUOTER = _Quoter(safe="@:", protected=":/@!$&'()*+,;=")
QUERY_QUOTER = _Quoter(safe="?/:@", protected="=+&;", qs=True, requote=False)
QUERY_REQUOTER = _Quoter(safe="?/:@", protected="=+&;", qs=True)
QUERY_PART_QUOTER = _Quoter(safe="?/:@", qs=True, requote=False)
FRAGMENT_QUOTER = _Quoter(safe="?/:@", requote=False)
FRAGMENT_REQUOTER = _Quoter(safe="?/:@")
# WHATWG mode keeps a "%" that does not start a "%XX" escape in parsed URLs,
# and "\\" as written: _backslashes() has read it as "/" where the URL is
# special, and "%5C" must stay encoded.
WHATWG_PATH_REQUOTER = _Quoter(
    safe="@:", protected=":/@!$&'()*+,;=\\", keep_invalid_pct=True
)
WHATWG_QUERY_REQUOTER = _Quoter(
    safe="?/:@", protected="=+&;\\", qs=True, keep_invalid_pct=True
)
WHATWG_FRAGMENT_REQUOTER = _Quoter(safe="?/:@", protected="\\", keep_invalid_pct=True)

# WHATWG mode keeps "\\" in the query and the fragment when it builds them
# from decoded values, as the parser does.
WHATWG_QUERY_QUOTER = _Quoter(safe="?/:@\\", protected="=+&;", qs=True, requote=False)
WHATWG_QUERY_PART_QUOTER = _Quoter(safe="?/:@\\", qs=True, requote=False)
WHATWG_FRAGMENT_QUOTER = _Quoter(safe="?/:@\\", requote=False)

UNQUOTER = _Unquoter()
PATH_SAFE_UNQUOTER = _Unquoter(ignore="/%")
# Keeps "%" and the delimiters of an authority encoded in a zone identifier.
ZONE_ID_UNQUOTER = _Unquoter(ignore="%/:?#[]@")
QS_UNQUOTER = _Unquoter(qs=True)
# to match urllib.parse.unquote_plus
UNQUOTER_PLUS = _Unquoter(plus=True, replace_invalid=True)


def human_quote(s: str | None, unsafe: str) -> str | None:
    if not s:
        return s
    for c in "%" + unsafe:
        if c in s:
            s = s.replace(c, f"%{ord(c):02X}")
    if s.isprintable():
        return s
    return "".join(c if c.isprintable() else quote(c) for c in s)
