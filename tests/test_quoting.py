import pytest

from yarl.quoting import quote, unquote


def hexescape(char):
    """Escape char as RFC 2396 specifies"""
    hex_repr = hex(ord(char))[2:].upper()
    if len(hex_repr) == 1:
        hex_repr = "0%s" % hex_repr
    return "%" + hex_repr


def test_quote_not_allowed():
    with pytest.raises(ValueError):
        quote('%HH')


def test_quote_unfinished():
    with pytest.raises(ValueError):
        quote('%F%F')


def test_quote_from_bytes():
    assert quote('archaeological arcana') == 'archaeological%20arcana'
    assert quote('') == ''


def test_unquote_to_bytes():
    assert unquote('abc%20def') == 'abc def'
    assert unquote('') == ''


def test_never_quote():
    # Make sure quote() does not quote letters, digits, and "_,.-"
    do_not_quote = '' .join(["ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                             "abcdefghijklmnopqrstuvwxyz",
                             "0123456789",
                             "_.-"])
    assert quote(do_not_quote) == do_not_quote
    quote(do_not_quote, plus=True) == do_not_quote


def test_safe():
    # Test setting 'safe' parameter does what it should do
    quote_by_default = "<>"
    assert quote(quote_by_default, safe=quote_by_default) == quote_by_default

    ret = quote(quote_by_default, safe=quote_by_default, plus=True)
    assert ret == quote_by_default


SHOULD_QUOTE = [chr(num) for num in range(32)]
SHOULD_QUOTE.append('<>#"{}|\^[]`')
SHOULD_QUOTE.append(chr(127))  # For 0x7F
SHOULD_QUOTE = ''.join(SHOULD_QUOTE)


@pytest.mark.parametrize('char', SHOULD_QUOTE)
def test_default_quoting(char):
    # Make sure all characters that should be quoted are by default sans
    # space (separate test for that).
    result = quote(char)
    assert hexescape(char) == result
    result = quote(char, plus=True)
    assert hexescape(char) == result


# TODO: should it encode percent?
def test_default_quoting_percent():
    result = quote('%25')
    assert '%25' == result
    result = quote('%25', plus=True)
    assert '%25' == result


def test_default_quoting_partial():
    partial_quote = "ab[]cd"
    expected = "ab%5B%5Dcd"
    result = quote(partial_quote)
    assert expected == result
    result = quote(partial_quote, plus=True)
    assert expected == result


def test_quoting_space():
    # Make sure quote() and quote_plus() handle spaces as specified in
    # their unique way
    result = quote(' ')
    assert result == hexescape(' ')
    result = quote(' ', plus=True)
    assert result == '+'

    given = "a b cd e f"
    expect = given.replace(' ', hexescape(' '))
    result = quote(given)
    assert expect == result
    expect = given.replace(' ', '+')
    result = quote(given, plus=True)
    assert expect == result


def test_quoting_plus():
    assert quote('alpha+beta gamma', plus=True) == 'alpha%2Bbeta+gamma'
    assert quote('alpha+beta gamma', safe='+', plus=True) == 'alpha+beta+gamma'


def test_quote_with_unicode():
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


def test_quote_plus_with_unicode():
    # Characters in Latin-1 range, encoded by default in UTF-8
    given = "\xa2\xd8ab\xff"
    expect = "%C2%A2%C3%98ab%C3%BF"
    result = quote(given, plus=True)
    assert expect == result
    # Characters in BMP, encoded by default in UTF-8
    given = "\u6f22\u5b57"              # "Kanji"
    expect = "%E6%BC%A2%E5%AD%97"
    result = quote(given, plus=True)
    assert expect == result


@pytest.mark.parametrize('num', list(range(128)))
def test_unquoting(num):
    # Make sure unquoting of all ASCII values works
    given = hexescape(chr(num))
    expect = chr(num)
    result = unquote(given)
    assert expect == result
    result = unquote(given, plus=True)
    assert expect == result


@pytest.mark.xfail
def test_unquoting_badpercent():
    # Test unquoting on bad percent-escapes
    given = '%xab'
    expect = given
    result = unquote(given)
    assert expect == result


@pytest.mark.xfail
def test_unquoting_badpercent2():
    given = '%x'
    expect = given
    result = unquote(given)
    assert expect == result


@pytest.mark.xfail
def test_unquoting_badpercent3():
    given = '%'
    expect = given
    result = unquote(given)
    assert expect == result


@pytest.mark.xfail
def test_unquoting_mixed_case():
    # Test unquoting on mixed-case hex digits in the percent-escapes
    given = '%Ab%eA'
    expect = '\xab\xea'
    result = unquote(given)
    assert expect == result


def test_unquoting_parts():
    # Make sure unquoting works when have non-quoted characters
    # interspersed
    given = 'ab%sd' % hexescape('c')
    expect = "abcd"
    result = unquote(given)
    assert expect == result
    result = unquote(given, plus=True)
    assert expect == result


def test_None():
    assert quote(None) is None
    assert unquote(None) is None


def test_empty_string():
    assert quote('') == ''
    assert unquote('') == ''


def test_bad_types():
    with pytest.raises(TypeError):
        quote(123)
    with pytest.raises(TypeError):
        unquote(123)
