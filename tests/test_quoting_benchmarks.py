from yarl._quoting import _Quoter, _Unquoter

QUOTER_SLASH_SAFE = _Quoter(safe="/")
QUOTER = _Quoter()
UNQUOTER = _Unquoter()


def test_quoter_ascii(benchmark):
    @benchmark
    def _run():
        for _ in range(100):
            QUOTER_SLASH_SAFE("/path/to")


def test_quoter_pct(benchmark):
    @benchmark
    def _run():
        for _ in range(100):
            QUOTER("abc%0a")


def test_quoter_quote(benchmark):
    @benchmark
    def _run():
        for _ in range(100):
            QUOTER("/шлях/файл")


def test_unquoter(benchmark):
    @benchmark
    def _run():
        for _ in range(100):
            UNQUOTER("/path/to")
