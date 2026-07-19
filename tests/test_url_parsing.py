from urllib.parse import SplitResult

import pytest

from yarl import URL


class TestScheme:
    def test_scheme_path(self) -> None:
        u = URL("scheme:path")
        assert u.scheme == "scheme"
        assert u.host is None
        assert u.path == "path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_scheme_path_other(self) -> None:
        u = URL("scheme:path:other")
        assert u.scheme == "scheme"
        assert u.host is None
        assert u.path == "path:other"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_complex_scheme(self) -> None:
        u = URL("allow+chars-33.:path")
        assert u.scheme == "allow+chars-33."
        assert u.host is None
        assert u.path == "path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_scheme_only(self) -> None:
        u = URL("simple:")
        assert u.scheme == "simple"
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == ""

    def test_no_scheme1(self) -> None:
        u = URL("google.com:80")
        assert u.scheme == "google.com"
        assert u.host is None
        assert u.path == "80"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_no_scheme2(self) -> None:
        u = URL("google.com:80/root")
        assert u.scheme == "google.com"
        assert u.host is None
        assert u.path == "80/root"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_not_a_scheme1(self) -> None:
        u = URL("not_cheme:path")
        assert u.scheme == ""
        assert u.host is None
        assert u.path == "not_cheme:path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_not_a_scheme2(self) -> None:
        u = URL("signals37:book")
        assert u.scheme == "signals37"
        assert u.host is None
        assert u.path == "book"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_scheme_rel_path1(self) -> None:
        u = URL(":relative-path")
        assert u.scheme == ""
        assert u.host is None
        assert u.path == ":relative-path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_scheme_rel_path2(self) -> None:
        u = URL(":relative/path")
        assert u.scheme == ""
        assert u.host is None
        assert u.path == ":relative/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_scheme_weird(self) -> None:
        u = URL("://and-this")
        assert u.scheme == ""
        assert u.host is None
        assert u.path == "://and-this"
        assert u.query_string == ""
        assert u.fragment == ""


class TestHost:
    def test_canonical(self) -> None:
        u = URL("scheme://host/path")
        assert u.scheme == "scheme"
        assert u.host == "host"
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_absolute_no_scheme(self) -> None:
        u = URL("//host/path")
        assert u.scheme == ""
        assert u.host == "host"
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_absolute_no_scheme_complex_host(self) -> None:
        u = URL("//host+path")
        assert u.scheme == ""
        assert u.host == "host+path"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_absolute_no_scheme_simple_host(self) -> None:
        u = URL("//host")
        assert u.scheme == ""
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_weird_host(self) -> None:
        u = URL("//this+is$also&host!")
        assert u.scheme == ""
        assert u.host == "this+is$also&host!"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_scheme_no_host(self) -> None:
        u = URL("scheme:/host/path")
        assert u.scheme == "scheme"
        assert u.host is None
        assert u.path == "/host/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_scheme_no_host2(self) -> None:
        u = URL("scheme:///host/path")
        assert u.scheme == "scheme"
        assert u.host is None
        assert u.path == "/host/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_no_scheme_no_host(self) -> None:
        u = URL("scheme//host/path")
        assert u.scheme == ""
        assert u.host is None
        assert u.path == "scheme//host/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_ipv4(self) -> None:
        u = URL("//127.0.0.1/")
        assert u.scheme == ""
        assert u.host == "127.0.0.1"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_ipv6(self) -> None:
        u = URL("//[::1]/")
        assert u.scheme == ""
        assert u.host == "::1"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_ipvfuture_address(self) -> None:
        u = URL("//[v1.-1]/")
        assert u.scheme == ""
        assert u.host == "v1.-1"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""


class TestPort:
    def test_canonical(self) -> None:
        u = URL("//host:80/path")
        assert u.scheme == ""
        assert u.host == "host"
        assert u.port == 80
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_no_path(self) -> None:
        u = URL("//host:80")
        assert u.scheme == ""
        assert u.host == "host"
        assert u.port == 80
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_no_host(self) -> None:
        u = URL("//:77")
        assert u.scheme == ""
        assert u.host == ""
        assert u.port == 77
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_double_port(self) -> None:
        with pytest.raises(ValueError):
            URL("//h:22:80/")

    def test_bad_port(self) -> None:
        with pytest.raises(ValueError):
            URL("//h:no/path")

    def test_another_bad_port(self) -> None:
        with pytest.raises(ValueError):
            URL("//h:22:no/path")

    def test_bad_port_again(self) -> None:
        with pytest.raises(ValueError):
            URL("//h:-80/path")


class TestUserInfo:
    def test_canonical(self) -> None:
        u = URL("sch://user@host/")
        assert u.scheme == "sch"
        assert u.user == "user"
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_user_pass(self) -> None:
        u = URL("//user:pass@host")
        assert u.scheme == ""
        assert u.user == "user"
        assert u.password == "pass"
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_complex_userinfo(self) -> None:
        u = URL("//user:pas:and:more@host")
        assert u.scheme == ""
        assert u.user == "user"
        assert u.password == "pas:and:more"
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_no_user(self) -> None:
        u = URL("//:pas:@host")
        assert u.scheme == ""
        assert u.user is None
        assert u.password == "pas:"
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_weird_user(self) -> None:
        u = URL("//!($&')*+,;=@host")
        assert u.scheme == ""
        assert u.user == "!($&')*+,;="
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_weird_user2(self) -> None:
        u = URL("//user@info@ya.ru")
        assert u.scheme == ""
        assert u.user == "user@info"
        assert u.password is None
        assert u.host == "ya.ru"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_weird_user3(self) -> None:
        u = URL("//%5Bsome%5D@host")
        assert u.scheme == ""
        assert u.user == "[some]"
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""


class TestQuery_String:
    def test_simple(self) -> None:
        u = URL("?query")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == "query"
        assert u.fragment == ""

    def test_scheme_query(self) -> None:
        u = URL("http:?query")
        assert u.scheme == "http"
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == "query"
        assert u.fragment == ""

    def test_abs_url_query(self) -> None:
        u = URL("//host?query")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == "query"
        assert u.fragment == ""

    def test_abs_url_path_query(self) -> None:
        u = URL("//host/path?query")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/path"
        assert u.query_string == "query"
        assert u.fragment == ""

    def test_double_question_mark(self) -> None:
        u = URL("//ho?st/path?query")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "ho"
        assert u.path == "/"
        assert u.query_string == "st/path?query"
        assert u.fragment == ""

    def test_complex_query(self) -> None:
        u = URL("?a://b:c@d.e/f?g#h")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == "a://b:c@d.e/f?g"
        assert u.fragment == "h"

    def test_query_in_fragment(self) -> None:
        u = URL("#?query")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == "?query"


class TestFragment:
    def test_simple(self) -> None:
        u = URL("#frag")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == "frag"

    def test_scheme_frag(self) -> None:
        u = URL("http:#frag")
        assert u.scheme == "http"
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == "frag"

    def test_host_frag(self) -> None:
        u = URL("//host#frag")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == "frag"

    def test_scheme_path_frag(self) -> None:
        u = URL("//host/path#frag")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == "frag"

    def test_scheme_query_frag(self) -> None:
        u = URL("//host?query#frag")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == "query"
        assert u.fragment == "frag"

    def test_host_frag_query(self) -> None:
        u = URL("//ho#st/path?query")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "ho"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == "st/path?query"

    def test_complex_frag(self) -> None:
        u = URL("#a://b:c@d.e/f?g#h")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == "a://b:c@d.e/f?g#h"


class TestStripEmptyParts:
    def test_all_empty_http(self) -> None:
        with pytest.raises(ValueError):
            URL("http://@:?#")

    def test_all_empty(self) -> None:
        u = URL("//@:?#")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == ""
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == ""

    def test_path_only(self) -> None:
        u = URL("///path")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_user(self) -> None:
        u = URL("//@host")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_port(self) -> None:
        u = URL("//host:")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_port_and_path(self) -> None:
        u = URL("//host:/")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host == "host"
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_path_only(self) -> None:
        u = URL("/")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == "/"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_relative_path_only(self) -> None:
        u = URL("path")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == "path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_path(self) -> None:
        u = URL("/path")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_query_with_path(self) -> None:
        u = URL("/path?")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_query(self) -> None:
        u = URL("?")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_query_with_frag(self) -> None:
        u = URL("?#frag")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == "frag"

    def test_path_empty_frag(self) -> None:
        u = URL("/path#")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == "/path"
        assert u.query_string == ""
        assert u.fragment == ""

    def test_empty_path(self) -> None:
        u = URL("#")
        assert u.scheme == ""
        assert u.user is None
        assert u.password is None
        assert u.host is None
        assert u.path == ""
        assert u.query_string == ""
        assert u.fragment == ""


@pytest.mark.parametrize(
    ("scheme"),
    [
        ("http"),
        ("https"),
        ("ws"),
        ("wss"),
        ("ftp"),
    ],
)
def test_schemes_that_require_host(scheme: str) -> None:
    """Verify that schemes that require a host raise with empty host."""
    expect = f"Invalid URL: host is required for absolute urls with the {scheme} scheme"
    with pytest.raises(ValueError, match=expect):
        URL(f"{scheme}://:1")


@pytest.mark.parametrize(
    ("url", "hostname", "hostname_without_brackets"),
    [
        ("http://[::1]", "[::1]", "::1"),
        ("http://[::1]:8080", "[::1]", "::1"),
        ("http://127.0.0.1:8080", "127.0.0.1", "127.0.0.1"),
        (
            "http://xn--jxagkqfkduily1i.eu",
            "xn--jxagkqfkduily1i.eu",
            "xn--jxagkqfkduily1i.eu",
        ),
    ],
)
def test_url_round_trips(
    url: str, hostname: str, hostname_without_brackets: str
) -> None:
    """Verify that URLs round-trip correctly."""
    parsed = URL(url)
    assert SplitResult(*parsed._val).hostname == hostname_without_brackets
    assert parsed.raw_host == hostname_without_brackets
    assert parsed.host_subcomponent == hostname
    assert str(parsed) == url
    assert str(URL(str(parsed))) == url


class TestPercentEncodedSchemeBypass:
    """Regression tests for parser/serializer inconsistency with percent-encoded schemes.

    When a URL contains a percent-encoded character in what would otherwise be a
    scheme (e.g. ``ht%74p://...``), the parser correctly treats it as a relative
    URL with no scheme. However, the requoter could decode the percent-encoding
    and materialize a scheme in the serialized output, creating a mismatch between
    parsed properties and ``str(url)`` / ``human_repr()``.

    See: https://github.com/aio-libs/yarl/issues/1661
    """

    @pytest.mark.parametrize(
        "input_url",
        [
            "ht%74p://127.0.0.1:8000/private",
            "ht%74ps://evil.example/path",
            "ja%76ascript:alert(1)",
            "data%3Atext/html,xss",
            "fi%6Ce:///etc/passwd",
            "HT%54P://example.com",
            "f%74p://files.example.com/pub",
        ],
        ids=[
            "http-pct-encoded-t",
            "https-pct-encoded-t",
            "javascript-pct-encoded-v",
            "data-pct-encoded-colon",
            "file-pct-encoded-l",
            "HTTP-uppercase-pct-encoded-T",
            "ftp-pct-encoded-t",
        ],
    )
    def test_str_does_not_introduce_scheme(self, input_url: str) -> None:
        """str(URL(x)) must not introduce a scheme absent from parsed components."""
        u = URL(input_url)
        assert u.scheme == ""
        assert u.host is None

        reparsed = URL(str(u))
        assert reparsed.scheme == u.scheme
        assert reparsed.host == u.host

    @pytest.mark.parametrize(
        "input_url",
        [
            "ht%74p://127.0.0.1:8000/private",
            "ht%74ps://evil.example/path",
            "ja%76ascript:alert(1)",
            "data%3Atext/html,xss",
            "fi%6Ce:///etc/passwd",
        ],
        ids=[
            "http-pct-encoded-t",
            "https-pct-encoded-t",
            "javascript-pct-encoded-v",
            "data-pct-encoded-colon",
            "file-pct-encoded-l",
        ],
    )
    def test_human_repr_does_not_introduce_scheme(self, input_url: str) -> None:
        """human_repr() must not introduce a scheme absent from parsed components."""
        u = URL(input_url)
        assert u.scheme == ""
        assert u.host is None

        reparsed = URL(u.human_repr())
        assert reparsed.scheme == u.scheme
        assert reparsed.host == u.host

    def test_reparse_consistency(self) -> None:
        """URL(str(URL(x))) must have the same security properties as URL(x)."""
        u = URL("ht%74p://127.0.0.1:8000/private")
        v = URL(str(u))

        assert u.scheme == v.scheme == ""
        assert u.host == v.host
        assert u.host is None
        assert u.raw_host == v.raw_host
        assert u.absolute == v.absolute is False

    def test_legitimate_scheme_not_affected(self) -> None:
        """Legitimate URLs with real schemes must not be affected."""
        u = URL("http://example.com/path")
        assert u.scheme == "http"
        assert u.host == "example.com"
        assert str(u) == "http://example.com/path"
        assert u.human_repr() == "http://example.com/path"

    def test_relative_path_with_colon_not_affected(self) -> None:
        """Relative paths with colons that aren't scheme-like must be preserved."""
        # "not_scheme:path"; underscore is not in scheme_chars, so not a scheme
        u = URL("not_scheme:path")
        assert u.scheme == ""
        assert str(u) == "not_scheme:path"

    def test_relative_path_no_colon_not_affected(self) -> None:
        """Simple relative paths without colons must be unaffected."""
        u = URL("relative/path")
        assert u.scheme == ""
        assert str(u) == "relative/path"
        assert u.human_repr() == "relative/path"

    def test_colon_in_later_segment_not_affected(self) -> None:
        """A colon in a later path segment (after /) is not a scheme delimiter."""
        u = URL("/path/with:colon")
        assert u.scheme == ""
        assert str(u) == "/path/with:colon"

    @pytest.mark.parametrize(
        "input_url",
        [
            "0t%65st:foo",
            "+ht%74p:foo",
            "-ht%74p:foo",
            ".ht%74p:foo",
        ],
        ids=[
            "digit-start",
            "plus-start",
            "minus-start",
            "dot-start",
        ],
    )
    def test_non_alpha_start_pct_encoded_does_not_materialize_scheme(
        self, input_url: str
    ) -> None:
        """split_url() accepts any scheme_chars in the first position, not just
        ALPHA, so digit / "+" / "-" / "." starts must also be guarded against
        scheme materialization on requote."""
        u = URL(input_url)
        assert u.scheme == ""
        assert u.host is None

        reparsed = URL(str(u))
        assert reparsed.scheme == u.scheme
        assert reparsed.host == u.host
        assert reparsed.absolute is False

    def test_relative_path_with_underscore_prefix_not_affected(self) -> None:
        """Prefixes that cannot form a scheme (contain chars outside
        scheme_chars) are left alone; the colon stays literal."""
        # underscore is not in scheme_chars, so "no_scheme:" cannot form a
        # scheme regardless of decoding.
        u = URL("no_sch%65me:foo")
        assert u.scheme == ""
        assert ":" in str(u)
        assert "%3A" not in str(u)


def test_raw_path_drops_lone_surrogate() -> None:
    """A lone surrogate in the path is dropped; raw_path stays ASCII."""
    url = URL("http://example.com/\ud800path")
    assert url.raw_path == "/path"
    # raw_path is always percent-encoded ASCII; a retained surrogate is a bug.
    assert url.raw_path.encode("ascii") == b"/path"
