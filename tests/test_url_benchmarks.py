"""codspeed benchmarks for yarl.URL."""

from pytest_codspeed import BenchmarkFixture  # type: ignore[import-untyped]

from yarl import URL

MANY_HOSTS = [f"www.domain{i}.tld" for i in range(256)]
MANY_URLS = [f"https://www.domain{i}.tld" for i in range(256)]
BASE_URL = URL("http://www.domain.tld")
URL_WITH_USER_PASS = URL("http://user:password@www.domain.tld")
IPV6_QUERY_URL = URL("http://[::1]/req?query=1&query=2&query=3&query=4&query=5")
URL_WITH_NOT_DEFAULT_PORT = URL("http://www.domain.tld:1234")
QUERY_URL = URL("http://www.domain.tld?query=1&query=2&query=3&query=4&query=5")
URL_WITH_PATH = URL("http://www.domain.tld/req")
REL_URL = URL("/req")
QUERY_SEQ = {str(i): tuple(str(j) for j in range(10)) for i in range(10)}
SIMPLE_QUERY = {str(i): str(i) for i in range(10)}
SIMPLE_INT_QUERY = {str(i): i for i in range(10)}


def test_url_build_with_host_and_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="www.domain.tld", path="/req", port=1234)


def test_url_build_encoded_with_host_and_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="www.domain.tld", path="/req", port=1234, encoded=True)


def test_url_build_with_host(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="domain")


def test_url_build_access_username_password(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld", user="user", password="password")
            url.raw_user
            url.raw_password


def test_url_build_access_raw_host(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld")
            url.raw_host


def test_url_build_access_fragment(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld")
            url.fragment


def test_url_build_access_raw_path(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL.build(host="www.domain.tld", path="/req")
            url.raw_path


def test_url_build_with_different_hosts(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for host in MANY_HOSTS:
            URL.build(host=host)


def test_url_build_with_host_path_and_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL.build(host="www.domain.tld", port=1234)


def test_url_make_with_host_path_and_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://www.domain.tld:1234/req")


def test_url_make_encoded_with_host_path_and_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://www.domain.tld:1234/req", encoded=True)


def test_url_make_with_host_and_path(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://www.domain.tld")


def test_url_make_with_many_hosts(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for url in MANY_URLS:
            URL(url)


def test_url_make_access_raw_host(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://www.domain.tld")
            url.raw_host


def test_url_make_access_fragment(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://www.domain.tld")
            url.fragment


def test_url_make_access_raw_path(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://www.domain.tld/req")
            url.raw_path


def test_url_make_access_username_password(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            url = URL("http://user:password@www.domain.tld")
            url.raw_user
            url.raw_password


def test_url_make_empty_username(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://:password@www.domain.tld")


def test_url_make_empty_password(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://user:@www.domain.tld")


def test_url_make_with_ipv4_address_path_and_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://127.0.0.1:1234/req")


def test_url_make_with_ipv4_address_and_path(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://127.0.0.1/req")


def test_url_make_with_ipv6_address_path_and_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://[::1]:1234/req")


def test_url_make_with_ipv6_address_and_path(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL("http://[::1]/req")


def test_url_make_with_query_mapping(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(SIMPLE_QUERY)


def test_url_make_with_int_query_mapping(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(SIMPLE_INT_QUERY)


def test_url_make_with_query_sequence_mapping(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.with_query(QUERY_SEQ)


def test_url_extend_query_simple_query_dict(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            BASE_URL.extend_query(SIMPLE_QUERY)


def test_url_extend_query_existing_query_simple_query_dict(
    benchmark: BenchmarkFixture,
) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            QUERY_URL.extend_query(SIMPLE_QUERY)


def test_url_extend_query_existing_query_string(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(25):
            QUERY_URL.extend_query("x=y&z=1")


def test_url_to_string(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            str(BASE_URL)


def test_url_with_path_to_string(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            str(URL_WITH_PATH)


def test_url_with_query_to_string(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            str(QUERY_URL)


def test_url_with_fragment(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_fragment("fragment")


def test_url_with_user(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_user("user")


def test_url_with_password(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_password("password")


def test_url_with_host(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_host("www.domain.tld")


def test_url_with_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_port(1234)


def test_url_with_scheme(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_scheme("https")


def test_url_with_path(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.with_path("/req")


def test_url_origin(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.origin()


def test_url_origin_with_user_pass(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL_WITH_USER_PASS.origin()


def test_url_with_path_origin(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL_WITH_PATH.origin()


def test_url_with_path_relative(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            URL_WITH_PATH.relative()


def test_url_join(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.join(REL_URL)


def test_url_joinpath_encoded(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.joinpath("req", encoded=True)


def test_url_joinpath_with_truediv(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL / "req/req/req"


def test_url_equality(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL == BASE_URL
            BASE_URL == URL_WITH_PATH
            URL_WITH_PATH == URL_WITH_PATH


def test_is_default_port(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.is_default_port()
            URL_WITH_NOT_DEFAULT_PORT.is_default_port()


def test_human_repr(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _run() -> None:
        for _ in range(100):
            BASE_URL.human_repr()
            URL_WITH_PATH.human_repr()
            QUERY_URL.human_repr()
            URL_WITH_NOT_DEFAULT_PORT.human_repr()
            IPV6_QUERY_URL.human_repr()
            REL_URL.human_repr()
