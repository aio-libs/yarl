"""codspeed benchmark for yarl._quoting module."""

from pytest_codspeed import BenchmarkFixture  # type: ignore[import-untyped]

from yarl._quoting import _Quoter, _Unquoter

QUOTER_SLASH_SAFE = _Quoter(safe="/")
QUOTER = _Quoter()
UNQUOTER = _Unquoter()
QUERY_QUOTER = _Quoter(safe="?/:@", protected="=+&;", qs=True, requote=False)

LONG_PATH = "/path/to" * 100
LONG_QUERY_ENCODED = "a=1&b=2&c=3&d=4&e=5&f=6&g=7&h=8&i=9&j=0" * 100
LONG_QUERY_ENCODED += "&d=%25%2F%3F%3A%40%26%3B%3D%2B"


def test_quote_query_string(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUERY_QUOTER("a=1&b=2&c=3&d=4&e=5&f=6&g=7&h=8&i=9&j=0")


def test_quoter_ascii(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER_SLASH_SAFE("/path/to")


def test_quote_long_path(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER(LONG_PATH)


def test_quoter_pct(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER("abc%0a")


def test_long_encoded_query(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUERY_QUOTER(LONG_QUERY_ENCODED)


def test_quoter_quote(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER("/шлях/файл")


def test_unquoter(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            UNQUOTER("/path/to")
