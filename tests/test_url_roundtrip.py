"""Property-based roundtrip tests for ``yarl.URL``.

These tests assert idempotency invariants — once ``URL`` has normalized
an input string, parsing the normalized form again must yield an equal
URL.  Likewise, components passed to ``URL.build`` must survive a
``str()`` -> ``URL()`` roundtrip when they only use characters that
``yarl`` does not transform.

The intent is to lock in the *current* normalization behavior, not to
exercise the parser with arbitrary input.  Alphabets are deliberately
restricted to characters that ``yarl`` never re-encodes; any future
change that breaks these invariants is almost certainly a regression.
"""

import pytest
from hypothesis import assume, example, given, note
from hypothesis import strategies as st

from yarl import URL

# Characters that survive ``yarl``'s default per-component quoting unchanged.
# All of these are members of RFC 3986 ``unreserved``.
_UNRESERVED = (
    "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "-._~"
)

# Schemes whose default ports yarl strips from ``str(URL)``.
_DEFAULT_PORTS = {"http": 80, "https": 443, "ws": 80, "wss": 443, "ftp": 21}


def _safe_text(min_size: int = 0, max_size: int = 30) -> st.SearchStrategy[str]:
    return st.text(alphabet=_UNRESERVED, min_size=min_size, max_size=max_size)


# ``.`` is unreserved but triggers RFC 3986 dot-segment normalization in
# paths (``/.`` collapses to ``/``).  Drop it from path alphabets so that
# roundtrip assertions are not falsified by intentional normalization.
_PATH_SAFE = _UNRESERVED.replace(".", "")


def _safe_path(min_size: int = 0, max_size: int = 30) -> st.SearchStrategy[str]:
    return st.text(alphabet=_PATH_SAFE, min_size=min_size, max_size=max_size)


def _assert_str_url_idempotent(url: str) -> None:
    first = URL(url)
    second = URL(str(first))
    assert first == second
    assert str(first) == str(second)
    assert hash(first) == hash(second)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/",
        "http://example.com/path?a=1&b=2#frag",
        "https://user:pass@example.com:8080/p?q=v#f",
    ],
)
def test_str_url_roundtrip_concrete_examples(url: str) -> None:
    """Sanity checks for ``str()`` -> ``URL()`` idempotency on real URLs."""
    _assert_str_url_idempotent(url)


@given(
    scheme=st.sampled_from(["http", "https", "ws", "wss", "ftp"]),
    host=_safe_text(min_size=1, max_size=20),
    path=_safe_path(max_size=30),
    query=_safe_text(max_size=20),
    fragment=_safe_text(max_size=20),
)
def test_str_url_roundtrip_is_idempotent(
    scheme: str,
    host: str,
    path: str,
    query: str,
    fragment: str,
) -> None:
    """``URL(str(URL(s)))`` must equal ``URL(s)`` (one-shot normalization)."""
    path_part = f"/{path}" if path else ""
    query_part = f"?k={query}" if query else ""
    fragment_part = f"#{fragment}" if fragment else ""
    url = f"{scheme}://{host}{path_part}{query_part}{fragment_part}"
    note(f"input url={url!r}")
    _assert_str_url_idempotent(url)


@given(
    scheme=st.sampled_from(["http", "https", "ws", "wss"]),
    host=_safe_text(min_size=1, max_size=20),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    path=_safe_path(max_size=30),
)
def test_build_components_survive_str_parse_roundtrip(
    scheme: str,
    host: str,
    port: int | None,
    path: str,
) -> None:
    """Components passed to ``URL.build`` are recovered after str/parse."""
    # Default ports for the given scheme are stripped from ``str(URL)``,
    # which is intentional per RFC 3986 section 6.2.3 — skip those cases.
    assume(port != _DEFAULT_PORTS.get(scheme))
    # ``URL.build`` expects absolute paths to start with ``/`` when there is
    # an authority component.
    if path and not path.startswith("/"):
        path = "/" + path
    built = URL.build(scheme=scheme, host=host, port=port, path=path)
    parsed = URL(str(built))
    assert parsed.scheme == scheme
    assert parsed.host == host.lower()
    assert parsed.explicit_port == port
    assert parsed.path == path or (path == "" and parsed.path in ("", "/"))
    assert parsed == built


@example(query_key="key", query_value="value")
@given(
    query_key=_safe_text(min_size=1, max_size=15),
    query_value=_safe_text(max_size=15),
)
def test_query_pair_survives_roundtrip(
    query_key: str,
    query_value: str,
) -> None:
    """A single safe key/value pair must roundtrip through ``str()``."""
    built = URL.build(
        scheme="https",
        host="example.com",
        query={query_key: query_value},
    )
    parsed = URL(str(built))
    assert parsed.query.get(query_key) == query_value
    assert parsed == built


@given(fragment=_safe_text(max_size=30))
def test_fragment_roundtrips(fragment: str) -> None:
    """Safe fragments are preserved verbatim."""
    built = URL.build(scheme="https", host="example.com", fragment=fragment)
    parsed = URL(str(built))
    assert parsed.fragment == fragment
    assert parsed == built


@example(s="http://example.com")
@example(s="http://example.com/")
@example(s="http://example.com:80/")  # default port stripped on str
@example(s="HTTP://Example.COM/PATH")  # scheme + host case folded
@given(
    s=st.builds(
        lambda scheme, host, path: f"{scheme}://{host}/{path}",
        scheme=st.sampled_from(["http", "https", "HTTP", "HTTPS"]),
        host=_safe_text(min_size=1, max_size=20),
        path=_safe_path(max_size=20),
    )
)
def test_repeated_normalization_reaches_fixed_point(s: str) -> None:
    """Normalization must be idempotent after at most one application."""
    once = str(URL(s))
    twice = str(URL(once))
    assert once == twice


@given(
    scheme=st.sampled_from(["http", "https"]),
    host=_safe_text(min_size=1, max_size=15),
    path=_safe_path(max_size=20),
)
def test_equal_urls_hash_equal(scheme: str, host: str, path: str) -> None:
    """Equal URLs must produce equal hashes (Python contract)."""
    path = "/" + path if path else ""
    u1 = URL.build(scheme=scheme, host=host, path=path)
    u2 = URL(str(u1))
    assume(u1 == u2)
    assert hash(u1) == hash(u2)
