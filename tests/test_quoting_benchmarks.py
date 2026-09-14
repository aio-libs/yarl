"""codspeed benchmark for yarl._quoting module."""

import pytest

try:
    from pytest_codspeed import BenchmarkFixture
except ImportError:  # pragma: no branch  # only hit in cibuildwheel
    pytestmark = pytest.mark.skip("pytest-codspeed needs to be installed")

from yarl._quoting import _Quoter, _Unquoter
from yarl._quoting_py import _Unquoter as _PyUnquoter

QUOTER_SLASH_SAFE = _Quoter(safe="/")
QUOTER = _Quoter()
UNQUOTER = _Unquoter()
UNQUOTER_PLUS = _Unquoter(plus=True)
QS_UNQUOTER = _Unquoter(qs=True)
PATH_SAFE_UNQUOTER = _Unquoter(ignore="/%", unsafe="+")
MULTI_UNSAFE_UNQUOTER = _Unquoter(unsafe="/@")
QUERY_QUOTER = _Quoter(safe="?/:@", protected="=+&;", qs=True, requote=False)
PATH_QUOTER = _Quoter(safe="@:", protected="/+", requote=False)

LONG_PATH = "/path/to" * 100
LONG_QUERY = "a=1&b=2&c=3&d=4&e=5&f=6&g=7&h=8&i=9&j=0" * 25
LONG_QUERY_WITH_PCT = LONG_QUERY + "&d=%25%2F%3F%3A%40%26%3B%3D%2B"
VERY_LONG_ASCII = "a" * 16384
VERY_LONG_ASCII_WITH_PCT = "%20" + VERY_LONG_ASCII
VERY_LONG_NON_ASCII = "\u65e5\u672c" * 8192
LONG_DENSE_PCT = "%C3%A9%20" * 1024
LONG_UTF8_TEXT_PCT = "%E6%97%A5%E6%9C%AC+text+%C3%A9t%C3%A9+" * 256
LONG_PLUS = "a+b" * 4096
LONG_PATH_WITH_PCT = "/path%20to/%E2%82%AC" * 256
LONG_PATH_WITH_ENCODED_DELIMS = "/a%2Fb/100%25+off%2Bsale%20%E2%82%AC" * 256
LONG_MULTI_UNSAFE = "user/name@" * 1024
FORM_TEXT_PCT = "Please+leave+the+package%2C+thanks%21+%E6%B3%A8%E6%96%87+" * 16


def test_quote_query_string(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUERY_QUOTER("a=1&b=2&c=3&d=4&e=5&f=6&g=7&h=8&i=9&j=0")


def test_quoter_ascii(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER_SLASH_SAFE("/path/to")


def test_quote_long_path(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            PATH_QUOTER(LONG_PATH)


def test_quoter_pct(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUOTER("abc%0a")


def test_long_query(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUERY_QUOTER(LONG_QUERY)


def test_long_query_with_pct(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QUERY_QUOTER(LONG_QUERY_WITH_PCT)


def test_quoter_quote_utf8(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            PATH_QUOTER("/шлях/файл")


def test_unquoter_short(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            UNQUOTER("/path/to")


def test_unquoter_long_ascii(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            UNQUOTER(LONG_QUERY)


def test_unquoter_long_pct(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            UNQUOTER(LONG_QUERY_WITH_PCT)


def test_unquoter_very_long_ascii(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            UNQUOTER(VERY_LONG_ASCII)


def test_unquoter_very_long_ascii_with_pct(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            UNQUOTER(VERY_LONG_ASCII_WITH_PCT)


def test_unquoter_very_long_non_ascii(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            UNQUOTER(VERY_LONG_NON_ASCII)


def test_unquoter_long_dense_pct(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            UNQUOTER(LONG_DENSE_PCT)


def test_unquoter_plus_long_utf8_text(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            UNQUOTER_PLUS(LONG_UTF8_TEXT_PCT)


def test_unquoter_plus_long_plus(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            UNQUOTER_PLUS(LONG_PLUS)


def test_qs_unquoter_long_pct(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            QS_UNQUOTER(LONG_QUERY_WITH_PCT)


def test_path_safe_unquoter_long_pct(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            PATH_SAFE_UNQUOTER(LONG_PATH_WITH_PCT)


def test_path_safe_unquoter_encoded_delims(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            PATH_SAFE_UNQUOTER(LONG_PATH_WITH_ENCODED_DELIMS)


def test_multi_unsafe_unquoter_long(benchmark: "BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(10):
            MULTI_UNSAFE_UNQUOTER(LONG_MULTI_UNSAFE)


# The pure Python unquoter is used on PyPy and when the C extension is not
# available; call it directly so it is measured even with the extension built.
PY_UNQUOTER_CASES = {
    "short": (_PyUnquoter(), "/path/to", 100),
    "long_ascii": (_PyUnquoter(), LONG_QUERY, 10),
    "long_pct": (_PyUnquoter(), LONG_QUERY_WITH_PCT, 10),
    "very_long_ascii": (_PyUnquoter(), VERY_LONG_ASCII, 1),
    "long_dense_pct": (_PyUnquoter(), LONG_DENSE_PCT, 1),
    "plus_form_text": (_PyUnquoter(plus=True), FORM_TEXT_PCT, 10),
    "plus_long_plus": (_PyUnquoter(plus=True), LONG_PLUS, 1),
    "qs_long_pct": (_PyUnquoter(qs=True), LONG_QUERY_WITH_PCT, 10),
    "path_safe_encoded_delims": (
        _PyUnquoter(ignore="/%", unsafe="+"),
        LONG_PATH_WITH_ENCODED_DELIMS,
        1,
    ),
    "multi_unsafe_long": (_PyUnquoter(unsafe="/@"), LONG_MULTI_UNSAFE, 1),
}


@pytest.mark.parametrize(
    ("unquoter", "value", "rounds"),
    PY_UNQUOTER_CASES.values(),
    ids=PY_UNQUOTER_CASES.keys(),
)
def test_py_unquoter(
    benchmark: "BenchmarkFixture", unquoter: _PyUnquoter, value: str, rounds: int
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(rounds):
            unquoter(value)
