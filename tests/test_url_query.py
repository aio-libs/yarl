from typing import List, Tuple
from urllib.parse import urlencode

import pytest
from multidict import MultiDict, MultiDictProxy

from yarl import URL

# ========================================
# Basic chars in query values
# ========================================

URLS_WITH_BASIC_QUERY_VALUES: List[Tuple[URL, MultiDict]] = [
    # Empty strings, keys and values
    (
        URL("http://example.com"),
        MultiDict(),
    ),
    (
        URL("http://example.com?a"),
        MultiDict([("a", "")]),
    ),
    (
        URL("http://example.com?a="),
        MultiDict([("a", "")]),
    ),
    # ASCII chars
    (
        URL("http://example.com?a+b=c+d"),
        MultiDict({"a b": "c d"}),
    ),
    (
        URL("http://example.com?a=1&b=2"),
        MultiDict([("a", "1"), ("b", "2")]),
    ),
    (
        URL("http://example.com?a=1&b=2&a=3"),
        MultiDict([("a", "1"), ("b", "2"), ("a", "3")]),
    ),
    # Non-ASCI BMP chars
    (
        URL("http://example.com?ключ=знач"),
        MultiDict({"ключ": "знач"}),
    ),
    (
        URL("http://example.com?foo=ᴜɴɪᴄᴏᴅᴇ"),
        MultiDict({"foo": "ᴜɴɪᴄᴏᴅᴇ"}),
    ),
    # Non-BMP chars
    (
        URL("http://example.com?bar=𝕦𝕟𝕚𝕔𝕠𝕕𝕖"),
        MultiDict({"bar": "𝕦𝕟𝕚𝕔𝕠𝕕𝕖"}),
    ),
]


@pytest.mark.parametrize(
    "original_url, expected_query",
    URLS_WITH_BASIC_QUERY_VALUES,
)
def test_query_basic_parsing(original_url, expected_query):
    assert isinstance(original_url.query, MultiDictProxy)
    assert original_url.query == expected_query


@pytest.mark.parametrize(
    "original_url, expected_query",
    URLS_WITH_BASIC_QUERY_VALUES,
)
def test_query_basic_update_query(original_url, expected_query):
    new_url = original_url.update_query({})
    # FIXME: `?a` becomes `?a=` right now. Maybe support `None` values?
    # assert new_url == original_url
    assert new_url is not None


def test_query_dont_unqoute_twice():
    sample_url = "http://base.place?" + urlencode({"a": "/////"})
    query = urlencode({"url": sample_url})
    full_url = "http://test_url.aha?" + query

    url = URL(full_url)
    assert url.query["url"] == sample_url


# ========================================
# Reserved chars in query values
# ========================================

URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES = [
    # Ampersand
    (URL("http://127.0.0.1/?a=10&b=20"), 2, "10"),
    (URL("http://127.0.0.1/?a=10%26b=20"), 1, "10&b=20"),
    (URL("http://127.0.0.1/?a=10%3Bb=20"), 1, "10;b=20"),
    # Semicolon
    (URL("http://127.0.0.1/?a=10;b=20"), 2, "10"),
    (URL("http://127.0.0.1/?a=10%26b=20"), 1, "10&b=20"),
    (URL("http://127.0.0.1/?a=10%3Bb=20"), 1, "10;b=20"),
]


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_separators_from_parsing(
    original_url,
    expected_query_len,
    expected_value_a,
):
    assert len(original_url.query) == expected_query_len
    assert original_url.query["a"] == expected_value_a


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_separators_from_update_query(
    original_url,
    expected_query_len,
    expected_value_a,
):
    new_url = original_url.update_query(
        {
            "c": expected_value_a,
        }
    )
    assert new_url.query["a"] == expected_value_a
    assert new_url.query["c"] == expected_value_a


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_separators_from_with_query(
    original_url,
    expected_query_len,
    expected_value_a,
):
    new_url = original_url.with_query(
        {
            "c": expected_value_a,
        }
    )
    assert new_url.query["c"] == expected_value_a


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_from_empty_update_query(
    original_url,
    expected_query_len,
    expected_value_a,
):
    new_url = original_url.update_query({})

    assert new_url.query["a"] == original_url.query["a"]

    if "b" in original_url.query:
        assert new_url.query["b"] == original_url.query["b"]

    # FIXME: Broken because of asymmetric query encoding
    # assert new_url == original_url
