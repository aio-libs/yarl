import pytest

from yarl import URL

MANY_HOSTS = [f"www.domain{i}.tld" for i in range(512)]
MANY_URLS = [f"https://www.domain{i}.tld" for i in range(512)]
BASE_URL = URL("http://www.domain.tld")
QUERY_URL = URL("http://www.domain.tld?query=1&query=2&query=3&query=4&query=5")
URL_WITH_PATH = URL("http://www.domain.tld/req")


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
    BASE_URL.with_query(
        {
            "a": "1",
            "b": "2",
            "c": "3",
            "d": "4",
            "e": "5",
            "f": "6",
            "g": "7",
            "h": "8",
            "i": "9",
            "j": "10",
        }
    )


@pytest.mark.benchmark
def test_url_make_with_query_sequence_mapping_performance():
    BASE_URL.with_query(
        {
            "0": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "1": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "2": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "3": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "4": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "5": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "6": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "7": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "8": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
            "9": ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
        }
    )


@pytest.mark.benchmark
def test_url_to_string_performance():
    str(BASE_URL)


@pytest.mark.benchmark
def test_url_with_path_to_string_performance():
    str(URL_WITH_PATH)


@pytest.mark.benchmark
def test_url_with_query_to_string_performance():
    str(QUERY_URL)
