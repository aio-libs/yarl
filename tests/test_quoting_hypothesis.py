"""Property-based quoting tests.

Split out from ``test_quoting.py`` so the wheel-build test run can execute the
rest of the suite without installing ``hypothesis`` (its tests are excluded
there via ``-m "not hypothesis"``). ``importorskip`` skips this module when
``hypothesis`` is not installed.
"""

from typing import TYPE_CHECKING, Any
from urllib.parse import quote, quote_plus, unquote_plus

import pytest

from yarl._quoting import NO_EXTENSIONS
from yarl._quoting_py import _Quoter as _PyQuoter
from yarl._quoting_py import _Unquoter as _PyUnquoter

if TYPE_CHECKING:
    from hypothesis import assume, example, given, note
    from hypothesis import strategies as st
else:
    pytest.importorskip("hypothesis")

    from hypothesis import assume, example, given, note
    from hypothesis import strategies as st

if not NO_EXTENSIONS:
    from yarl._quoting_c import _Quoter as _CQuoter  # type: ignore[import-not-found]
    from yarl._quoting_c import _Unquoter as _CUnquoter

    quoters = [_PyQuoter, _CQuoter]
    quoter_ids = ["PyQuoter", "CQuoter"]
    unquoters = [_PyUnquoter, _CUnquoter]
    unquoter_ids = ["PyUnquoter", "CUnquoter"]
else:
    quoters = [_PyQuoter]
    quoter_ids = ["PyQuoter"]
    unquoters = [_PyUnquoter]
    unquoter_ids = ["PyUnquoter"]


@given(safe=st.text(), protected=st.text(), qs=st.booleans(), requote=st.booleans())
def test_fuzz__PyQuoter(safe: str, protected: str, qs: bool, requote: bool) -> None:  # type: ignore[misc]
    """Verify that _PyQuoter can be instantiated with any valid arguments."""
    _PyQuoter(safe=safe, protected=protected, qs=qs, requote=requote)


@given(ignore=st.text(), qs=st.booleans())
def test_fuzz__PyUnquoter(ignore: str, qs: bool) -> None:  # type: ignore[misc]
    """Verify that _PyUnquoter can be instantiated with any valid arguments."""
    _PyUnquoter(ignore=ignore, qs=qs)


@example(text_input="0")
@given(
    text_input=st.text(
        alphabet=st.characters(max_codepoint=127, blacklist_characters="%")
    ),
)
@pytest.mark.parametrize("quoter", quoters, ids=quoter_ids)
@pytest.mark.parametrize("unquoter", unquoters, ids=unquoter_ids)
def test_quote_unquote_parameter(  # type: ignore[misc]
    quoter: type[_PyQuoter],
    unquoter: type[_PyUnquoter],
    text_input: str,
) -> None:
    quote = quoter()
    unquote = unquoter()
    text_quoted = quote(text_input)
    note(f"text_quoted={text_quoted!r}")
    text_output = unquote(text_quoted)
    assert text_input == text_output


@example(text_input="0")
@given(
    text_input=st.text(
        alphabet=st.characters(max_codepoint=127, blacklist_characters="%")
    ),
)
@pytest.mark.parametrize("quoter", quoters, ids=quoter_ids)
@pytest.mark.parametrize("unquoter", unquoters, ids=unquoter_ids)
def test_quote_unquote_parameter_requote(  # type: ignore[misc]
    quoter: type[_PyQuoter],
    unquoter: type[_PyUnquoter],
    text_input: str,
) -> None:
    quote = quoter(requote=True)
    unquote = unquoter()
    text_quoted = quote(text_input)
    note(f"text_quoted={text_quoted!r}")
    text_output = unquote(text_quoted)
    assert text_input == text_output


@example(text_input="0")
@given(
    text_input=st.text(
        alphabet=st.characters(max_codepoint=127, blacklist_characters="%")
    ),
)
@pytest.mark.parametrize("quoter", quoters, ids=quoter_ids)
@pytest.mark.parametrize("unquoter", unquoters, ids=unquoter_ids)
def test_quote_unquote_parameter_path_safe(  # type: ignore[misc]
    quoter: type[_PyQuoter],
    unquoter: type[_PyUnquoter],
    text_input: str,
) -> None:
    quote = quoter()
    unquote = unquoter(ignore="/%")
    assume("/" not in text_input)
    text_quoted = quote(text_input)
    note(f"text_quoted={text_quoted!r}")
    text_output = unquote(text_quoted)
    assert text_input == text_output


# The unquoter configurations used by yarl itself, see yarl/_quoters.py
UNQUOTER_KWARGS = [
    {},
    {"ignore": "/%"},
    {"qs": True},
    {"plus": True},
]

_LONG_RUN = st.integers(min_value=0, max_value=5000).map(lambda n: "a" * n)
_NO_SURROGATE_TEXT = st.text(alphabet=st.characters(codec="utf-8"))
_QUOTED = _NO_SURROGATE_TEXT.map(quote)
# Plain text, long runs, and every kind of escape the unquoter handles,
# including invalid and incomplete UTF-8 sequences.
_UNQUOTE_PIECES = st.one_of(
    st.text(),
    _LONG_RUN,
    _QUOTED,
    st.sampled_from(
        [
            "%",
            "+",
            "/",
            "=",
            "&",
            ";",
            "%2B",
            "%2b",
            "%25",
            "%2F",
            "%3D",
            "%26",
            "%e2%82",
            "%e2%82%ac",
            "%ff",
            "%C3",
            "%ed%a0%80",
            "%c0%af",  # overlong 2 byte
            "%e0%80%af",  # overlong 3 byte
            "%f0%80%80%af",  # overlong 4 byte
            "%f4%90%80%80",  # above U+10FFFF
            "%f0%9f%98",  # truncated 4 byte
            "%4",
            "%zz",
            "%%41",
        ]
    ),
)


@pytest.mark.skipif(NO_EXTENSIONS, reason="Extensions not available")
@pytest.mark.parametrize("kwargs", UNQUOTER_KWARGS)
@given(pieces=st.lists(_UNQUOTE_PIECES))
def test_c_and_py_unquoter_match(  # type: ignore[misc]
    kwargs: dict[str, Any], pieces: list[str]
) -> None:
    val = "".join(pieces)
    assert _CUnquoter(**kwargs)(val) == _PyUnquoter(**kwargs)(val)


# Characters that change how the unquoter behaves when they are in ignore,
# plus ones that do nothing special, so any configuration is covered and not
# just the ones in yarl/_quoters.py.
_CONFIG_CHARS = [
    " ",
    "+",
    "%",
    "/",
    "@",
    "=",
    "&",
    ";",
    "?",
    "#",
    "!",
    ":",
    "\t",
    "a",
    "Z",
    "0",
]
_ANY_CONFIG_PIECES = st.one_of(
    _UNQUOTE_PIECES,
    st.sampled_from(_CONFIG_CHARS),
    st.sampled_from(
        [
            "%20",
            "%40",
            "%3F",
            "%23",
            "%21",
            "%3A",
            "%3B",
            "%09",
            "%61",
            "%C3%A9",
            "%E6%97%A5",
        ]
    ),
)


@pytest.mark.skipif(NO_EXTENSIONS, reason="Extensions not available")
@example(pieces=["a+b%20c"], ignore=" ", qs=True, plus=False)
@example(pieces=["a+b%20c"], ignore=" ", qs=False, plus=True)
@given(
    pieces=st.lists(_ANY_CONFIG_PIECES),
    ignore=st.text(alphabet=st.sampled_from([*_CONFIG_CHARS, "é", "日"]), max_size=4),
    qs=st.booleans(),
    plus=st.booleans(),
)
def test_c_and_py_unquoter_match_any_config(  # type: ignore[misc]
    pieces: list[str], ignore: str, qs: bool, plus: bool
) -> None:
    val = "".join(pieces)
    c_unquoter = _CUnquoter(ignore=ignore, qs=qs, plus=plus)
    py_unquoter = _PyUnquoter(ignore=ignore, qs=qs, plus=plus)
    assert c_unquoter(val) == py_unquoter(val)


# Pieces never form an incomplete or invalid UTF-8 escape (text pieces
# exclude '%', quote() emits whole sequences, %zz is not an escape), so
# urllib.parse.unquote_plus agrees with yarl
_VALID_UNQUOTE_PIECES = st.one_of(
    st.text(alphabet=st.characters(blacklist_characters="%")),
    _LONG_RUN,
    _QUOTED,
    _NO_SURROGATE_TEXT.map(quote_plus),
    st.sampled_from(["+", "%2B", "%25", "%zz"]),
)


@pytest.mark.parametrize("unquoter", unquoters, ids=unquoter_ids)
@given(pieces=st.lists(_VALID_UNQUOTE_PIECES))
def test_unquoter_plus_matches_unquote_plus(  # type: ignore[misc]
    unquoter: type[_PyUnquoter], pieces: list[str]
) -> None:
    val = "".join(pieces)
    assert unquoter(plus=True)(val) == unquote_plus(val)
