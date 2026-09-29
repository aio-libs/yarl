import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from yarl._quoting import NO_EXTENSIONS, _Quoter, _Unquoter

FREE_THREADING_ENABLED: bool = hasattr(sys, "_is_gil_enabled") and sys._is_gil_enabled()
ft_mark = pytest.mark.skipif(not FREE_THREADING_ENABLED, NO_EXTENSIONS, reason="free threading not enabled")


@pytest.fixture(params=[_Quoter], ids=["c_quoter"])
def quoter(request: pytest.FixtureRequest) -> _Quoter:  # type: ignore[no-any-unimported,misc,unused-ignore]
    return request.param

@pytest.fixture(params=[_Unquoter], ids=["c_unquoter"])
def unquoter(request: pytest.FixtureRequest) -> _Unquoter:  # type: ignore[no-any-unimported,misc,unused-ignore]
    return request.param

@ft_mark
def test_quoter_concurrency(quoter:type[_Quoter]) -> None:
    PAIRS = {
        "%HH": "%25HH",
        "%": "%25",
        "%2": "%252",
        "%x": "%25x",
        "%#": "%25%23",
        "%ß": "%25%C3%9F",
        "%€": "%25%E2%82%AC",
        "%🐍": "%25%F0%9F%90%8D",
        "archaeological arcana": "archaeological%20arcana"
    }
    q = quoter()

    def quote(item: str):
        return q(item) == PAIRS[item]

    with ThreadPoolExecutor(3) as te:
        assert all(te.map(quote(PAIRS)))

@ft_mark
def test_unquoter_concurrency(unquoter: type[_Unquoter]) -> None:
    PAIRS = {
        "%": "%",
        "%2": "%2",
        "%x": "%x",
        "%€": "%€",
        "%2x": "%2x",
        "%2 ": "%2 ",
        "% 2": "% 2",
        "%xa": "%xa",
        "%%": "%%",
        "%%3f": "%?",
        "%2%": "%2%",
        "%2%3f": "%2?",
        "%x%3f": "%x?",
        "%€%3f": "%€?",
    }

    q = unquoter()
    
    def unquote(item: str):
        return q(item) == PAIRS[item]

    with ThreadPoolExecutor(3) as te:
        assert all(te.map(unquote, PAIRS))



