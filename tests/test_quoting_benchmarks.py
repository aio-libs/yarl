import pytest

from yarl._quoting import _Quoter, _Unquoter

QUOTER_SLASH_SAFE = _Quoter(safe="/")
QUOTER = _Quoter()
UNQUOTER = _Unquoter()


@pytest.mark.benchmark
def test_quoter_ascii():
    for _ in range(100):
        QUOTER_SLASH_SAFE("/path/to")


@pytest.mark.benchmark
def test_quoter_pct():
    for _ in range(100):
        QUOTER("abc%0a")


@pytest.mark.benchmark
def test_quoter_quote():
    for _ in range(100):
        QUOTER("/шлях/файл")


@pytest.mark.benchmark
def test_unquoter():
    for _ in range(100):
        UNQUOTER("/path/to")
