import pytest

from yarl._quoting import _Quoter, _Unquoter

QUOTER_SLASH_SAFE = _Quoter(safe="/")
QUOTER = _Quoter()
UNQUOTER = _Unquoter()


@pytest.mark.benchmark
def test_quoter_ascii():
    QUOTER_SLASH_SAFE("/path/to")


@pytest.mark.benchmark
def test_quoter_pct():
    QUOTER("abc%0a")


@pytest.mark.benchmark
def test_quoter_quote():
    QUOTER("/шлях/файл")


@pytest.mark.benchmark
def test_unquoter():
    UNQUOTER("/path/to")
