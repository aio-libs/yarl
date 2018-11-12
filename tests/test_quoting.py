import pytest

from yarl.quoting import _PyQuoter, _PyUnquoter, _Quoter, _Unquoter


@pytest.fixture(params=[_PyQuoter, _Quoter], ids=["py_quoter", "c_quoter"])
def quoter(request):
    return request.param


@pytest.fixture(params=[_PyUnquoter, _Unquoter], ids=["py_unquoter", "c_unquoter"])
def unquoter(request):
    return request.param


def hexescape(char):
    """Escape char as RFC 2396 specifies"""
    hex_repr = hex(ord(char))[2:].upper()
    if len(hex_repr) == 1:
        hex_repr = "0%s" % hex_repr
    return "%" + hex_repr


def test_quote_not_allowed_non_strict(quoter):
    assert quoter()("%HH") == "%25HH"


def test_quote_unfinished_tail_percent_non_strict(quoter):
    assert quoter()("%") == "%25"


def test_quote_unfinished_tail_non_strict(quoter):
    assert quoter()("%2") == "%252"


def test_quote_from_bytes(quoter):
    assert quoter()("archaeological arcana") == "archaeological%20arcana"
    assert quoter()("") == ""


def test_quote_ignore_broken_unicode(quoter):
    s = quoter()(
        "j\u001a\udcf4q\udcda/\udc97g\udcee\udccb\u000ch\udccb"
        "\u0018\udce4v\u001b\udce2\udcce\udccecom/y\udccepj\u0016"
    )

    assert s == "j%1Aq%2Fg%0Ch%18v%1Bcom%2Fypj%16"
    assert quoter()(s) == s


def test_unquote_to_bytes(unquoter):
    assert unquoter()("abc%20def") == "abc def"
    assert unquoter()("") == ""


def test_never_quote(quoter):
    # Make sure quote() does not quote letters, digits, and "_,.-~"
    do_not_quote = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "abcdefghijklmnopqrstuvwxyz" "0123456789" "_.-~"
    )
    assert quoter()(do_not_quote) == do_not_quote
    assert quoter(qs=True)(do_not_quote) == do_not_quote


def test_safe(quoter):
    # Test setting 'safe' parameter does what it should do
    quote_by_default = "<>"
    assert quoter(safe=quote_by_default)(quote_by_default) == quote_by_default

    ret = quoter(safe=quote_by_default, qs=True)(quote_by_default)
    assert ret == quote_by_default


_SHOULD_QUOTE = [chr(num) for num in range(32)]
_SHOULD_QUOTE.append(r'<>#"{}|\^[]`')
_SHOULD_QUOTE.append(chr(127))  # For 0x7F
SHOULD_QUOTE = "".join(_SHOULD_QUOTE)


@pytest.mark.parametrize("char", SHOULD_QUOTE)
def test_default_quoting(char, quoter):
    # Make sure all characters that should be quoted are by default sans
    # space (separate test for that).
    result = quoter()(char)
    assert hexescape(char) == result
    result = quoter(qs=True)(char)
    assert hexescape(char) == result


# TODO: should it encode percent?
def test_default_quoting_percent(quoter):
    result = quoter()("%25")
    assert "%25" == result
    result = quoter(qs=True)("%25")
    assert "%25" == result


def test_default_quoting_partial(quoter):
    partial_quote = "ab[]cd"
    expected = "ab%5B%5Dcd"
    result = quoter()(partial_quote)
    assert expected == result
    result = quoter(qs=True)(partial_quote)
    assert expected == result


def test_quoting_space(quoter):
    # Make sure quote() and quote_plus() handle spaces as specified in
    # their unique way
    result = quoter()(" ")
    assert result == hexescape(" ")
    result = quoter(qs=True)(" ")
    assert result == "+"

    given = "a b cd e f"
    expect = given.replace(" ", hexescape(" "))
    result = quoter()(given)
    assert expect == result
    expect = given.replace(" ", "+")
    result = quoter(qs=True)(given)
    assert expect == result


def test_quoting_plus(quoter):
    assert quoter(qs=False)("alpha+beta gamma") == "alpha+beta%20gamma"
    assert quoter(qs=True)("alpha+beta gamma") == "alpha%2Bbeta+gamma"
    assert quoter(safe="+", qs=True)("alpha+beta gamma") == "alpha+beta+gamma"


def test_quote_with_unicode(quoter):
    # Characters in Latin-1 range, encoded by default in UTF-8
    given = "\u00a2\u00d8ab\u00ff"
    expect = "%C2%A2%C3%98ab%C3%BF"
    result = quoter()(given)
    assert expect == result
    # Characters in BMP, encoded by default in UTF-8
    given = "\u6f22\u5b57"  # "Kanji"
    expect = "%E6%BC%A2%E5%AD%97"
    result = quoter()(given)
    assert expect == result


def test_quote_plus_with_unicode(quoter):
    # Characters in Latin-1 range, encoded by default in UTF-8
    given = "\u00a2\u00d8ab\u00ff"
    expect = "%C2%A2%C3%98ab%C3%BF"
    result = quoter(qs=True)(given)
    assert expect == result
    # Characters in BMP, encoded by default in UTF-8
    given = "\u6f22\u5b57"  # "Kanji"
    expect = "%E6%BC%A2%E5%AD%97"
    result = quoter(qs=True)(given)
    assert expect == result


@pytest.mark.parametrize("num", list(range(128)))
def test_unquoting(num, unquoter):
    # Make sure unquoting of all ASCII values works
    given = hexescape(chr(num))
    expect = chr(num)
    result = unquoter()(given)
    assert expect == result
    if expect not in "+=&;":
        result = unquoter(qs=True)(given)
        assert expect == result


@pytest.mark.xfail
# FIXME: Expected value should be the same as given.
# See https://url.spec.whatwg.org/#percent-encoded-bytes
def test_unquoting_bad_percent_escapes_1(unquoter):
    assert "%" == unquoter()("%")


@pytest.mark.xfail
# FIXME: Expected value should be the same as given.
# See https://url.spec.whatwg.org/#percent-encoded-bytes
def test_unquoting_bad_percent_escapes_2(unquoter):
    assert "%x" == unquoter()("%x")


@pytest.mark.xfail
# FIXME: Expected value should be the same as given.
# See https://url.spec.whatwg.org/#percent-encoded-bytes
def test_unquoting_bad_percent_escapes_3(unquoter):
    assert "%xa" == unquoter()("%xa")


@pytest.mark.xfail
# FIXME: After conversion to bytes, should not cause UTF-8 decode fail.
# See https://url.spec.whatwg.org/#percent-encoded-bytes
def test_unquoting_invalid_utf8_sequence(unquoter):
    with pytest.raises(ValueError):
        unquoter()("%AB")
    with pytest.raises(ValueError):
        unquoter()("%AB%AB")


def test_unquoting_mixed_case_percent_escapes(unquoter):
    expected = "𝕦"
    assert expected == unquoter()("%F0%9D%95%A6")
    assert expected == unquoter()("%F0%9d%95%a6")
    assert expected == unquoter()("%f0%9D%95%a6")
    assert expected == unquoter()("%f0%9d%95%a6")


def test_unquoting_parts(unquoter):
    # Make sure unquoting works when have non-quoted characters
    # interspersed
    given = "ab" + hexescape("c") + "d"
    expect = "abcd"
    result = unquoter()(given)
    assert expect == result
    result = unquoter(qs=True)(given)
    assert expect == result


def test_quote_None(quoter):
    assert quoter()(None) is None


def test_unquote_None(unquoter):
    assert unquoter()(None) is None


def test_quote_empty_string(quoter):
    assert quoter()("") == ""


def test_unquote_empty_string(unquoter):
    assert unquoter()("") == ""


def test_quote_bad_types(quoter):
    with pytest.raises(TypeError):
        quoter()(123)


def test_unquote_bad_types(unquoter):
    with pytest.raises(TypeError):
        unquoter()(123)


def test_quote_lowercase(quoter):
    assert quoter()("%d1%84") == "%D1%84"


def test_quote_unquoted(quoter):
    assert quoter()("%41") == "A"


def test_quote_space(quoter):
    assert quoter()(" ") == "%20"  # NULL


# test to see if this would work to fix
# coverage on this file.
def test_quote_percent_last_character(quoter):
    # % is last character in this case.
    assert quoter()("%") == "%25"


def test_unquote_unsafe(unquoter):
    assert unquoter(unsafe="@")("%40") == "%40"


def test_unquote_unsafe2(unquoter):
    assert unquoter(unsafe="@")("%40abc") == "%40abc"


def test_unquote_unsafe3(unquoter):
    assert unquoter(qs=True)("a%2Bb=?%3D%2B%26") == "a%2Bb=?%3D%2B%26"


def test_unquote_unsafe4(unquoter):
    assert unquoter(unsafe="@")("a@b") == "a%40b"


def test_unquote_non_ascii(unquoter):
    assert unquoter()("%F8") == "%F8"


def test_unquote_non_ascii_non_tailing(unquoter):
    assert unquoter()("%F8ab") == "%F8ab"


def test_quote_non_ascii(quoter):
    assert quoter()("%F8") == "%F8"


def test_quote_non_ascii2(quoter):
    assert quoter()("a%F8b") == "a%F8b"


class StrLike(str):
    pass


def test_quote_str_like(quoter):
    assert quoter()(StrLike("abc")) == "abc"


def test_unquote_str_like(unquoter):
    assert unquoter()(StrLike("abc")) == "abc"


def test_quote_sub_delims(quoter):
    assert quoter()("!$&'()*+,;=") == "!$&'()*+,;="


def test_requote_sub_delims(quoter):
    assert quoter()("%21%24%26%27%28%29%2A%2B%2C%3B%3D") == "!$&'()*+,;="


def test_unquoting_plus(unquoter):
    assert unquoter(qs=False)("a+b") == "a+b"


def test_unquote_plus_to_space(unquoter):
    assert unquoter(qs=True)("a+b") == "a b"


def test_unquote_plus_to_space_unsafe(unquoter):
    assert unquoter(unsafe="+", qs=True)("a+b") == "a+b"


def test_qoute_qs_with_colon(quoter):
    s = quoter(safe="=+&?/:@", qs=True)("next=http%3A//example.com/")
    assert s == "next=http://example.com/"


def test_quote_protected(quoter):
    s = quoter(protected="/")("/path%2fto/three")
    assert s == "/path%2Fto/three"


def test_quote_fastpath_safe():
    s1 = "/path/to"
    s2 = _Quoter(safe="/")(s1)
    assert s1 is s2


def test_quote_fastpath_pct():
    s1 = "abc%A0"
    s2 = _Quoter()(s1)
    assert s1 is s2


def test_quote_very_large_string(quoter):
    # more than 8 KiB
    s = "abcфух%30%0a" * 1024
    assert quoter()(s) == "abc%D1%84%D1%83%D1%850%0A" * 1024


def test_space(quoter):
    s = "% A"
    assert quoter()(s) == "%25%20A"
