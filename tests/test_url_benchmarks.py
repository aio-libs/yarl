import pytest

from yarl import URL

MANY_HOSTS = [f"www.domain{i}.tld" for i in range(512)]
MANY_URLS = [f"https://www.domain{i}.tld" for i in range(512)]
BASE_URL = URL("http://www.domain.tld")
QUERY_URL = URL("http://www.domain.tld?query=1&query=2&query=3&query=4&query=5")
URL_WITH_PATH = URL("http://www.domain.tld/req")
_QUERY_SEQ = {str(i): (str(j) for j in range(10)) for i in range(10)}
_SIMPLE_QUERY = {str(i): str(i) for i in range(10)}


@pytest.mark.benchmark
def test_url_build_with_host_and_port_performance():
    URL.build(host="www.domain.tld", path="/req", port=1234)


@pytest.mark.benchmark
def test_url_build_encoded_with_host_and_port_performance():
    URL.build(host="www.domain.tld", path="/req", port=1234, encoded=True)


@pytest.mark.benchmark
def test_url_build_with_host_performance():
    URL.build(host="domain")


@pytest.mark.benchmark
def test_url_build_with_different_hosts_performance():
    for host in MANY_HOSTS:
        URL.build(host=host)


@pytest.mark.benchmark
def test_url_build_with_host_path_and_port_performance():
    URL.build(host="www.domain.tld", port=1234)


@pytest.mark.benchmark
def test_url_make_with_host_path_and_port_performance():
    URL("http://www.domain.tld:1234/req")


@pytest.mark.benchmark
def test_url_make_encoded_with_host_path_and_port_performance():
    URL("http://www.domain.tld:1234/req", encoded=True)


@pytest.mark.benchmark
def test_url_make_with_host_and_path_performance():
    URL("http://www.domain.tld")


@pytest.mark.benchmark
def test_url_make_with_many_hosts_performance():
    for url in MANY_URLS:
        URL(url)


@pytest.mark.benchmark
def test_url_make_with_ipv4_address_path_and_port_performance():
    URL("http://127.0.0.1:1234/req")


@pytest.mark.benchmark
def test_url_make_with_ipv4_address_and_path_performance():
    URL("http://127.0.0.1/req")


@pytest.mark.benchmark
def test_url_make_with_ipv6_address_path_and_port_performance():
    URL("http://[::1]:1234/req")


@pytest.mark.benchmark
def test_url_make_with_ipv6_address_and_path_performance():
    URL("http://[::1]/req")


@pytest.mark.benchmark
def test_url_make_with_query_mapping_performance():
    BASE_URL.with_query(_SIMPLE_QUERY)


@pytest.mark.benchmark
def test_url_make_with_query_sequence_mapping_performance():
    BASE_URL.with_query(_QUERY_SEQ)


@pytest.mark.benchmark
def test_url_to_string_performance():
    str(BASE_URL)


@pytest.mark.benchmark
def test_url_with_path_to_string_performance():
    str(URL_WITH_PATH)


@pytest.mark.benchmark
def test_url_with_query_to_string_performance():
    str(QUERY_URL)
