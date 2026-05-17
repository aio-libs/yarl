from collections.abc import Sequence
from urllib.parse import parse_qs, urlencode

import pytest
from multidict import MultiDict, MultiDictProxy

from yarl import URL

# ========================================
# Basic chars in query values
# ========================================

URLS_WITH_BASIC_QUERY_VALUES: list[tuple[URL, MultiDict[str]]] = [
    # Empty strings, keys and values
    (
        URL("http://example.com"),
        MultiDict(),
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
def test_query_basic_parsing(original_url: URL, expected_query: MultiDict[str]) -> None:
    assert isinstance(original_url.query, MultiDictProxy)
    assert original_url.query == expected_query


@pytest.mark.parametrize(
    "original_url, expected_query",
    URLS_WITH_BASIC_QUERY_VALUES,
)
def test_query_basic_update_query(
    original_url: URL, expected_query: MultiDict[str]
) -> None:
    new_url = original_url.update_query({})
    assert new_url == original_url


def test_query_dont_unqoute_twice() -> None:
    sample_url = "http://base.place?" + urlencode({"a": "/////"})
    query = urlencode({"url": sample_url})
    full_url = "http://test_url.aha?" + query

    url = URL(full_url)
    assert url.query["url"] == sample_url


# ========================================
# Reserved chars in query values
# ========================================

# See https://github.com/python/cpython#87133, which introduced a new
# `separator` keyword argument to `urllib.parse.parse_qs` (among others).
# If the name doesn't exist as a variable in the function bytecode, the
# test is expected to fail.
_SEMICOLON_XFAIL = pytest.mark.xfail(
    condition="separator" not in parse_qs.__code__.co_varnames,
    reason=(
        "Python versions < 3.9.2 lack a fix for "
        'CVE-2021-23336 dropping ";" as a valid query parameter separator, '
        "making this test fail."
    ),
    strict=True,
)


URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES = [
    # Ampersand
    (URL("http://127.0.0.1/?a=10&b=20"), 2, "10"),
    (URL("http://127.0.0.1/?a=10%26b=20"), 1, "10&b=20"),
    (URL("http://127.0.0.1/?a=10%3Bb=20"), 1, "10;b=20"),
    # Semicolon, which is *not* a query parameter separator as of RFC3986
    (URL("http://127.0.0.1/?a=10;b=20"), 1, "10;b=20"),
    (URL("http://127.0.0.1/?a=10%26b=20"), 1, "10&b=20"),
    (URL("http://127.0.0.1/?a=10%3Bb=20"), 1, "10;b=20"),
]
URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES_W_XFAIL = [
    # Ampersand
    *URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES[:3],
    # Semicolon, which is *not* a query parameter separator as of RFC3986
    # Mark the first of these as expecting to fail on old Python patch releases.
    pytest.param(*URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES[3], marks=_SEMICOLON_XFAIL),
    *URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES[4:],
]


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES_W_XFAIL,
)
def test_query_separators_from_parsing(
    original_url: URL,
    expected_query_len: int,
    expected_value_a: str,
) -> None:
    assert len(original_url.query) == expected_query_len
    assert original_url.query["a"] == expected_value_a


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES_W_XFAIL,
)
def test_query_separators_from_update_query(
    original_url: URL,
    expected_query_len: int,
    expected_value_a: str,
) -> None:
    new_url = original_url.update_query({"c": expected_value_a})
    assert new_url.query["a"] == expected_value_a
    assert new_url.query["c"] == expected_value_a


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_separators_from_with_query(
    original_url: URL,
    expected_query_len: int,
    expected_value_a: str,
) -> None:
    new_url = original_url.with_query({"c": expected_value_a})
    assert new_url.query["c"] == expected_value_a


@pytest.mark.parametrize(
    "original_url, expected_query_len, expected_value_a",
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_from_empty_update_query(
    original_url: URL,
    expected_query_len: int,
    expected_value_a: str,
) -> None:
    new_url = original_url.update_query({})

    assert new_url.query["a"] == original_url.query["a"]

    if "b" in original_url.query:
        assert new_url.query["b"] == original_url.query["b"]


@pytest.mark.parametrize(
    ("original_query_string", "keys_to_drop", "expected_query_string"),
    [
        ("a=10&b=M%C3%B9a+xu%C3%A2n&u%E1%BB%91ng=cafe", ["a"], "b=Mùa xuân&uống=cafe"),
        ("a=10&b=M%C3%B9a+xu%C3%A2n", ["b"], "a=10"),
        ("a=10&b=M%C3%B9a+xu%C3%A2n&c=30", ["b"], "a=10&c=30"),
        (
            "a=10&b=M%C3%B9a+xu%C3%A2n&u%E1%BB%91ng=cafe",
            ["uống"],
            "a=10&b=Mùa xuân",
        ),
        ("a=10&b=M%C3%B9a+xu%C3%A2n", ["a", "b"], ""),
    ],
)
def test_without_query_params(
    original_query_string: str, keys_to_drop: Sequence[str], expected_query_string: str
) -> None:
    url = URL(f"http://example.com?{original_query_string}")
    new_url = url.without_query_params(*keys_to_drop)
    assert new_url.query_string == expected_query_string
    assert new_url is not url


@pytest.mark.parametrize(
    ("original_query_string", "keys_to_drop"),
    [
        ("a=10&b=M%C3%B9a+xu%C3%A2n&c=30", ["invalid_key"]),
        ("a=10&b=M%C3%B9a+xu%C3%A2n", []),
    ],
)
def test_skip_dropping_query_params(
    original_query_string: str, keys_to_drop: Sequence[str]
) -> None:
    url = URL(f"http://example.com?{original_query_string}")
    new_url = url.without_query_params(*keys_to_drop)
    assert new_url is url


def test_update_query_rejects_bytes() -> None:
    url = URL("http://example.com")
    with pytest.raises(TypeError):
        url.update_query(b"foo=bar")  # type: ignore[arg-type]


def test_update_query_rejects_bytearray() -> None:
    url = URL("http://example.com")
    with pytest.raises(TypeError):
        url.update_query(bytearray(b"foo=bar"))  # type: ignore[arg-type]


def test_update_query_rejects_memoryview() -> None:
    url = URL("http://example.com")
    with pytest.raises(TypeError):
        url.update_query(memoryview(b"foo=bar"))


def test_update_query_rejects_invalid_type() -> None:
    url = URL("http://example.com")
    with pytest.raises(TypeError):
        url.update_query(42)  # type: ignore[call-overload]


def test_update_query_with_sequence_of_pairs() -> None:
    url = URL("http://example.com")
    new_url = url.update_query([("a", "1"), ("b", "2")])
    assert new_url.query == MultiDict([("a", "1"), ("b", "2")])
    assert new_url.query_string == "a=1&b=2"


@pytest.mark.parametrize(
    "query",
    [
        {"x": ":/?#[]@!$&'()*+,;="},
        [("x", ":/?#[]@!$&'()*+,;=")],
    ],
)
def test_query_arguments_percent_encode_reserved_chars_except_bang_and_question(
    query: dict[str, str] | list[tuple[str, str]],
) -> None:
    url = URL("https://example.com").with_query(query)
    assert (
        url.raw_query_string == "x=%3A%2F?%23%5B%5D%40!%24%26%27%28%29%2A%2B%2C%3B%3D"
    )
    assert url.query["x"] == ":/?#[]@!$&'()*+,;="


def test_query_arguments_percent_encode_issue_1073_reproducer() -> None:
    query = {"deviceUdid": '${"freemarker.template.utility.Execute"?new()("ls")}'}
    url = URL.build(scheme="https", host="foo", query=query)
    assert (
        str(url) == "https://foo/?deviceUdid="
        "%24%7B%22freemarker.template.utility.Execute%22?new%28%29%28%22ls%22%29%7D"
    )
    assert URL(str(url)) == url
    assert url.query["deviceUdid"] == query["deviceUdid"]


def test_literal_query_string_preserves_reserved_delimiters() -> None:
    url = URL.build(
        scheme="https",
        host="foo",
        query="foo=ba=r&next=http://example.com/p?a",
    )
    assert str(url) == "https://foo/?foo=ba=r&next=http://example.com/p?a"
