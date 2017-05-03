import pytest

from yarl.quoting import _py_quote, _py_unquote, _quote, _unquote


@pytest.fixture(params=[_py_quote, _quote], ids=['py_quote', 'c_quote'])
def quote(request):
    return request.param


@pytest.fixture(params=[_py_unquote, _unquote],
                ids=['py_unquote', 'c_unquote'])
def unquote(request):
    return request.param


def hexescape(char):
    """Escape char as RFC 2396 specifies"""
    hex_repr = hex(ord(char))[2:].upper()
    if len(hex_repr) == 1:
        hex_repr = "0%s" % hex_repr
    return "%" + hex_repr


def test_quote_not_allowed(quote):
    with pytest.raises(ValueError):
        quote('%HH')


def test_quote_not_allowed_non_strict(quote):
    assert quote('%HH', strict=False) == '%25HH'


def test_quote_unfinished(quote):
    with pytest.raises(ValueError):
        quote('%F%F')


def test_quote_unfinished_tail_percent(quote):
    with pytest.raises(ValueError):
        quote('%')


def test_quote_unfinished_tail_percent_non_strict(quote):
    assert quote('%', strict=False) == '%25'


def test_quote_unfinished_tail(quote):
    with pytest.raises(ValueError):
        quote('%2')


def test_quote_unfinished_tail_non_strict(quote):
    assert quote('%2', strict=False) == '%252'


def test_quote_from_bytes(quote):
    assert quote('archaeological arcana') == 'archaeological%20arcana'
    assert quote('') == ''


def test_quate_broken_unicode(quote):
    with pytest.raises(UnicodeEncodeError):
        quote('j\x1a\udcf4q\udcda/\udc97g\udcee\udccb\x0ch\udccb'
              '\x18\udce4v\x1b\udce2\udcce\udccecom/y\udccepj\x16')


def test_quate_ignore_broken_unicode(quote):
    s = quote('j\x1a\udcf4q\udcda/\udc97g\udcee\udccb\x0ch\udccb'
              '\x18\udce4v\x1b\udce2\udcce\udccecom/y\udccepj\x16',
              strict=False)

    assert s == 'j%1Aq%2Fg%0Ch%18v%1Bcom%2Fypj%16'


def test_unquote_to_bytes(unquote):
    assert unquote('abc%20def') == 'abc def'
    assert unquote('') == ''


def test_never_quote(quote):
    # Make sure quote() does not quote letters, digits, and "_,.-"
    do_not_quote = '' .join(["ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                             "abcdefghijklmnopqrstuvwxyz",
                             "0123456789",
                             "_.-"])
    assert quote(do_not_quote) == do_not_quote
    quote(do_not_quote, qs=True) == do_not_quote


def test_safe(quote):
    # Test setting 'safe' parameter does what it should do
    quote_by_default = "<>"
    assert quote(quote_by_default, safe=quote_by_default) == quote_by_default

    ret = quote(quote_by_default, safe=quote_by_default, qs=True)
    assert ret == quote_by_default


SHOULD_QUOTE = [chr(num) for num in range(32)]
SHOULD_QUOTE.append('<>#"{}|\^[]`')
SHOULD_QUOTE.append(chr(127))  # For 0x7F
SHOULD_QUOTE = ''.join(SHOULD_QUOTE)


@pytest.mark.parametrize('char', SHOULD_QUOTE)
def test_default_quoting(char, quote):
    # Make sure all characters that should be quoted are by default sans
    # space (separate test for that).
    result = quote(char)
    assert hexescape(char) == result
    result = quote(char, qs=True)
    assert hexescape(char) == result


# TODO: should it encode percent?
def test_default_quoting_percent(quote):
    result = quote('%25')
    assert '%25' == result
    result = quote('%25', qs=True)
    assert '%25' == result


def test_default_quoting_partial(quote):
    partial_quote = "ab[]cd"
    expected = "ab%5B%5Dcd"
    result = quote(partial_quote)
    assert expected == result
    result = quote(partial_quote, qs=True)
    assert expected == result


def test_quoting_space(quote):
    # Make sure quote() and quote_plus() handle spaces as specified in
    # their unique way
    result = quote(' ')
    assert result == hexescape(' ')
    result = quote(' ', qs=True)
    assert result == '+'

    given = "a b cd e f"
    expect = given.replace(' ', hexescape(' '))
    result = quote(given)
    assert expect == result
    expect = given.replace(' ', '+')
    result = quote(given, qs=True)
    assert expect == result


def test_quoting_plus(quote):
    assert quote('alpha+beta gamma', qs=False) == 'alpha+beta%20gamma'
    assert quote('alpha+beta gamma', qs=True) == 'alpha%2Bbeta+gamma'
    assert quote('alpha+beta gamma', safe='+', qs=True) == 'alpha+beta+gamma'


def test_quote_with_unicode(quote):
    # Characters in Latin-1 range, encoded by default in UTF-8
    given = "\xa2\xd8ab\xff"
    expect = "%C2%A2%C3%98ab%C3%BF"
    result = quote(given)
    assert expect == result
    # Characters in BMP, encoded by default in UTF-8
    given = "\u6f22\u5b57"              # "Kanji"
    expect = "%E6%BC%A2%E5%AD%97"
    result = quote(given)
    assert expect == result


def test_quote_plus_with_unicode(quote):
    # Characters in Latin-1 range, encoded by default in UTF-8
    given = "\xa2\xd8ab\xff"
    expect = "%C2%A2%C3%98ab%C3%BF"
    result = quote(given, qs=True)
    assert expect == result
    # Characters in BMP, encoded by default in UTF-8
    given = "\u6f22\u5b57"              # "Kanji"
    expect = "%E6%BC%A2%E5%AD%97"
    result = quote(given, qs=True)
    assert expect == result


@pytest.mark.parametrize('num', list(range(128)))
def test_unquoting(num, unquote):
    # Make sure unquoting of all ASCII values works
    given = hexescape(chr(num))
    expect = chr(num)
    result = unquote(given)
    assert expect == result
    if expect not in '+=&;':
        result = unquote(given, qs=True)
        assert expect == result


@pytest.mark.xfail
def test_unquoting_badpercent(unquote):
    # Test unquoting on bad percent-escapes
    given = '%xab'
    expect = given
    result = unquote(given)
    assert expect == result


@pytest.mark.xfail
def test_unquoting_badpercent2(unquote):
    given = '%x'
    expect = given
    result = unquote(given)
    assert expect == result


@pytest.mark.xfail
def test_unquoting_badpercent3(unquote):
    given = '%'
    expect = given
    result = unquote(given)
    assert expect == result


@pytest.mark.xfail
def test_unquoting_mixed_case(unquote):
    # Test unquoting on mixed-case hex digits in the percent-escapes
    given = '%Ab%eA'
    expect = '\xab\xea'
    result = unquote(given)
    assert expect == result


def test_unquoting_parts(unquote):
    # Make sure unquoting works when have non-quoted characters
    # interspersed
    given = 'ab%sd' % hexescape('c')
    expect = "abcd"
    result = unquote(given)
    assert expect == result
    result = unquote(given, qs=True)
    assert expect == result


def test_quote_None(quote):
    assert quote(None) is None


def test_unquote_None(unquote):
    assert unquote(None) is None


def test_quote_empty_string(quote):
    assert quote('') == ''


def test_unempty_string(unquote):
    assert unquote('') == ''


def test_quote_bad_types(quote):
    with pytest.raises(TypeError):
        quote(123)


def test_unquote_bad_types(unquote):
    with pytest.raises(TypeError):
        unquote(123)


def test_quote_lowercase(quote):
    assert quote('%d1%84') == '%D1%84'


def test_quote_unquoted(quote):
    assert quote('%41') == 'A'


def test_quote_space(quote):
    assert quote(' ', strict=False) == '%20'  # NULL


# test to see if this would work to fix
# coverage on this file.
def test_quote_percent_last_character(quote):
    # % is last character in this case.
    assert quote('%', strict=False) == '%25'


def test_unquote_unsafe(unquote):
    assert unquote('%40', unsafe='@') == '%40'


def test_unquote_unsafe2(unquote):
    assert unquote('%40abc', unsafe='@') == '%40abc'


def test_unquote_unsafe3(unquote):
    assert unquote('a%2Bb=?%3D%2B%26', qs=True) == 'a%2Bb=?%3D%2B%26'


def test_unquote_unsafe4(unquote):
    assert unquote('a@b', unsafe='@') == 'a%40b'


def test_unquote_non_ascii(unquote):
    assert unquote('%F8') == '%F8'


def test_unquote_non_ascii_non_tailing(unquote):
    assert unquote('%F8ab') == '%F8ab'


def test_quote_non_ascii(quote):
    assert quote('%F8') == '%F8'


def test_quote_non_ascii2(quote):
    assert quote('a%F8b') == 'a%F8b'


class StrLike(str):
    pass


def test_quote_str_like(quote):
    assert quote(StrLike('abc')) == 'abc'


def test_unquote_str_like(unquote):
    assert unquote(StrLike('abc')) == 'abc'


def test_quote_sub_delims(quote):
    assert quote("!$&'()*+,;=") == "!$&'()*+,;="


def test_requote_sub_delims(quote):
    assert quote("%21%24%26%27%28%29%2A%2B%2C%3B%3D") == "!$&'()*+,;="


def test_unquoting_plus(unquote):
    assert unquote('a+b', qs=False) == 'a+b'


def test_unquote_plus_to_space(unquote):
    assert unquote('a+b', qs=True) == 'a b'


def test_unquote_plus_to_space_unsafe(unquote):
    assert unquote('a+b', unsafe='+', qs=True) == 'a+b'


def test_qoute_qs_with_colon(quote):
    s = quote('next=http%3A//example.com/', safe='=+&?/:@', qs=True)
    assert s == 'next=http://example.com/'


def test_quote_protected(quote):
    s = quote('/path%2fto/three', protected='/')
    assert s == '/path%2Fto/three'
