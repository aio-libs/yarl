"""codspeed benchmarks for yarl.URL."""

import pytest

from yarl import URL

pytest_codspeed = pytest.importorskip("pytest_codspeed")


MANY_HOSTS = [f"www.domain{i}.tld" for i in range(256)]
MANY_URLS = [f"https://www.domain{i}.tld" for i in range(256)]
MANY_IPV4_URLS = [f"http://127.0.0.{i}" for i in range(256)]
MANY_IPV6_URLS = [f"http://[::1{i}]" for i in range(256)]
BASE_URL_STR = "http://www.domain.tld"
BASE_URL = URL(BASE_URL_STR)
URL_WITH_USER_PASS_STR = "http://user:password@www.domain.tld"
URL_WITH_USER_PASS = URL(URL_WITH_USER_PASS_STR)
IPV6_QUERY_URL = URL("http://[::1]/req?query=1&query=2&query=3&query=4&query=5")
URL_WITH_NOT_DEFAULT_PORT = URL("http://www.domain.tld:1234")
QUERY_URL_STR = "http://www.domain.tld?query=1&query=2&query=3&query=4&query=5"
QUERY_URL = URL(QUERY_URL_STR)
URL_WITH_PATH_STR = "http://www.domain.tld/req"
URL_WITH_PATH = URL(URL_WITH_PATH_STR)
REL_URL = URL("/req")
QUERY_SEQ = {str(i): tuple(str(j) for j in range(10)) for i in range(10)}
SIMPLE_QUERY = {str(i): str(i) for i in range(10)}
SIMPLE_INT_QUERY = {str(i): i for i in range(10)}
QUERY_STRING = "x=y&z=1"


class _SubClassedStr(str):
    """A subclass of str that does nothing."""


def test_url_build_with_host_and_port(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="www.domain.tld", path="/req", port=1234)


def test_url_build_with_simple_query(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="www.domain.tld", query=SIMPLE_QUERY)


def test_url_build_no_netloc(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(path="/req/req/req")


def test_url_build_no_netloc_relative(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(path="req/req/req")


def test_url_build_encoded_with_host_and_port(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="www.domain.tld", path="/req", port=1234, encoded=True)


def test_url_build_with_host(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="domain")


def test_url_build_access_username_password(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld", user="user", password="password")
            url.raw_user
            url.raw_password


def test_url_build_access_raw_host(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld")
            url.raw_host


def test_url_build_access_fragment(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld")
            url.fragment


def test_url_build_access_raw_path(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld", path="/req")
            url.raw_path


def test_url_build_with_different_hosts(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for host in MANY_HOSTS:
            URL.build(host=host)


def test_url_build_with_host_path_and_port(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="www.domain.tld", port=1234)


def test_url_make_no_netloc(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("/req/req/req")


def test_url_make_no_netloc_relative(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("req/req/req")


def test_url_make_with_host_path_and_port(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://www.domain.tld:1234/req")


def test_url_make_encoded_with_host_path_and_port(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://www.domain.tld:1234/req", encoded=True)


def test_url_make_with_host_and_path(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://www.domain.tld")


def test_url_make_with_many_hosts(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for url in MANY_URLS:
            URL(url)


def test_url_make_with_many_ipv4_hosts(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for url in MANY_IPV4_URLS:
            URL(url)


def test_url_make_with_many_ipv6_hosts(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for url in MANY_IPV6_URLS:
            URL(url)


def test_url_make_access_raw_host(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://www.domain.tld")
            url.raw_host


def test_raw_host_empty_cache(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    url = URL("http://www.domain.tld")

    @benchmark
    def _run() -> None:
        for _ in range(100):
            url._cache.pop("raw_host", None)
            url.raw_host


def test_url_make_access_fragment(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://www.domain.tld")
            url.fragment


def test_url_make_access_raw_path(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://www.domain.tld/req")
            url.raw_path


def test_url_make_access_username_password(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://user:password@www.domain.tld")
            url.raw_user
            url.raw_password


def test_url_make_empty_username(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://:password@www.domain.tld")


def test_url_make_empty_password(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://user:@www.domain.tld")


def test_url_make_with_ipv4_address_path_and_port(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://127.0.0.1:1234/req")


def test_url_make_with_ipv4_address_and_path(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://127.0.0.1/req")


def test_url_make_with_ipv6_address_path_and_port(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://[::1]:1234/req")


def test_url_make_with_ipv6_address_and_path(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://[::1]/req")


def test_extend_query_subclassed_str(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    """Test extending a query with a subclassed str."""
    subclassed_query = {str(i): _SubClassedStr(i) for i in range(10)}

    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(subclassed_query)


def test_with_query_mapping(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(SIMPLE_QUERY)


def test_with_query_mapping_int_values(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(SIMPLE_INT_QUERY)


def test_with_query_sequence_mapping(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(QUERY_SEQ)


def test_with_query_empty(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query({})


def test_with_query_none(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(None)


def test_update_query_mapping(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.update_query(SIMPLE_QUERY)


def test_update_query_mapping_with_existing_query(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            QUERY_URL.update_query(SIMPLE_QUERY)


def test_update_query_sequence_mapping(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.update_query(QUERY_SEQ)


def test_update_query_empty(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.update_query({})


def test_update_query_none(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.update_query(None)


def test_update_query_string(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.update_query(QUERY_STRING)


def test_url_extend_query_simple_query_dict(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.extend_query(SIMPLE_QUERY)


def test_url_extend_query_existing_query_simple_query_dict(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            QUERY_URL.extend_query(SIMPLE_QUERY)


def test_url_extend_query_existing_query_string(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            QUERY_URL.extend_query(QUERY_STRING)


def test_url_to_string(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            str(BASE_URL)


def test_url_with_path_to_string(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            str(URL_WITH_PATH)


def test_url_with_query_to_string(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            str(QUERY_URL)


def test_url_with_fragment(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_fragment("fragment")


def test_url_with_user(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_user("user")


def test_url_with_password(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_password("password")


def test_url_with_host(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_host("www.domain.tld")


def test_url_with_port(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_port(1234)


def test_url_with_scheme(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_scheme("https")


def test_url_with_name(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_name("other.tld")


def test_url_with_path(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_path("/req")


def test_url_origin(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    urls = [URL(BASE_URL_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            url.origin()


def test_url_origin_with_user_pass(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    urls = [URL(URL_WITH_USER_PASS_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            url.origin()


def test_url_with_path_origin(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    urls = [URL(URL_WITH_PATH_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            url.origin()


def test_url_with_path_relative(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL_WITH_PATH.relative()


def test_url_with_path_parent(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    cache = URL_WITH_PATH._cache

    @benchmark
    def _run() -> None:
        for _ in range(100):
            cache.pop("parent", None)
            URL_WITH_PATH.parent


def test_url_join(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.join(REL_URL)


def test_url_joinpath_encoded(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.joinpath("req", encoded=True)


def test_url_joinpath_encoded_long(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.joinpath(
                "req/req/req/req/req/req/req/req/req/req/req/req/req/req", encoded=True
            )


def test_url_joinpath(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.joinpath("req", encoded=False)


def test_url_joinpath_with_truediv(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL / "req/req/req"


def test_url_equality(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL == BASE_URL
            BASE_URL == URL_WITH_PATH
            URL_WITH_PATH == URL_WITH_PATH


def test_url_hash(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    cache = BASE_URL._cache

    @benchmark
    def _run() -> None:
        for _ in range(100):
            cache.pop("hash", None)
            hash(BASE_URL)


def test_is_default_port(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.is_default_port()
            URL_WITH_NOT_DEFAULT_PORT.is_default_port()


def test_human_repr(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.human_repr()
            URL_WITH_PATH.human_repr()
            QUERY_URL.human_repr()
            URL_WITH_NOT_DEFAULT_PORT.human_repr()
            IPV6_QUERY_URL.human_repr()
            REL_URL.human_repr()


def test_query_string(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    urls = [URL(QUERY_URL_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            url.query_string


def test_empty_query_string(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    urls = [URL(BASE_URL_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            url.query_string


def test_empty_query_string_uncached(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    urls = [URL(BASE_URL_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            URL.query_string.wrapped(url)


def test_query(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    urls = [URL(QUERY_URL_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            url.query


def test_empty_query(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    urls = [URL(BASE_URL_STR) for _ in range(100)]

    @benchmark
    def _run() -> None:
        for url in urls:
            url.query


def test_url_host_port_subcomponent(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    cache_non_default = URL_WITH_NOT_DEFAULT_PORT._cache
    cache = BASE_URL._cache

    @benchmark
    def _run() -> None:
        for _ in range(100):
            cache.pop("host_port_subcomponent", None)
            cache_non_default.pop("host_port_subcomponent", None)
            URL_WITH_NOT_DEFAULT_PORT.host_port_subcomponent
            BASE_URL.host_port_subcomponent


def test_empty_path(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing empty path."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.path


def test_empty_path_uncached(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing empty path without cache."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.path.wrapped(BASE_URL)


def test_empty_path_safe(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing empty path safe."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.path_safe


def test_empty_path_safe_uncached(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    """Test accessing empty path safe without cache."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.path_safe.wrapped(BASE_URL)


def test_path_safe(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing path safe."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL_WITH_PATH.path_safe


def test_path_safe_uncached(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing path safe without cache."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.path_safe.wrapped(URL_WITH_PATH)


def test_empty_raw_path_qs(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing empty raw path with query."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.raw_path_qs


def test_empty_raw_path_qs_uncached(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    """Test accessing empty raw path with query without cache."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.raw_path_qs.wrapped(BASE_URL)


def test_raw_path_qs(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing raw path qs without query."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL_WITH_PATH.raw_path_qs


def test_raw_path_qs_uncached(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing raw path qs without query and without cache."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.raw_path_qs.wrapped(URL_WITH_PATH)


def test_raw_path_qs_with_query(benchmark: "pytest_codspeed.BenchmarkFixture") -> None:
    """Test accessing raw path qs with query."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            IPV6_QUERY_URL.raw_path_qs


def test_raw_path_qs_with_query_uncached(
    benchmark: "pytest_codspeed.BenchmarkFixture",
) -> None:
    """Test accessing raw path qs with query and without cache."""

    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.raw_path_qs.wrapped(IPV6_QUERY_URL)
