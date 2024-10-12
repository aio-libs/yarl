"""codspeed benchmark for yarl._quoting module."""

from pytest_codspeed import BenchmarkFixture  # type: ignore[import-untyped]

from yarl._quoting import _Quoter, _Unquoter

QUOTER_SLASH_SAFE = _Quoter(safe="/")
QUOTER = _Quoter()
UNQUOTER = _Unquoter()


def test_quoter_ascii(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER_SLASH_SAFE("/path/to")


def test_quoter_pct(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER("abc%0a")


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
