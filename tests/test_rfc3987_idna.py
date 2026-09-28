"""Conformance tests for internationalized identifiers.

* RFC 3987, Internationalized Resource Identifiers (IRIs):
  https://www.rfc-editor.org/rfc/rfc3987
* RFC 3492, Punycode:
  https://www.rfc-editor.org/rfc/rfc3492
* RFC 5891 and RFC 5892, IDNA2008, with the UTS #46 mapping step:
  https://www.rfc-editor.org/rfc/rfc5891
  https://www.unicode.org/reports/tr46/

yarl encodes non-ASCII hosts with IDNA2008 plus the UTS #46 mapping and
falls back to IDNA2003 only when that fails.
"""

import pytest

from yarl import URL


def diverges(reason: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(strict=True, reason=f"yarl: {reason}")


# RFC 3987 section 3.1: an IRI maps to a URI by converting the host to
# punycode and percent-encoding the UTF-8 octets of everything else.
@pytest.mark.parametrize(
    ("iri", "uri"),
    [
        (
            "http://résumé.example.org",
            "http://xn--rsum-bpad.example.org",
        ),
        (
            "http://www.example.org/Dürst",
            "http://www.example.org/D%C3%BCrst",
        ),
        (
            "http://пример.рф/путь?к=в#ф",
            "http://xn--e1afmkfd.xn--p1ai/%D0%BF%D1%83%D1%82%D1%8C"
            "?%D0%BA=%D0%B2#%D1%84",
        ),
        (
            "http://example.com/\U0001f600",
            "http://example.com/%F0%9F%98%80",
        ),
    ],
)
def test_iri_to_uri(iri: str, uri: str) -> None:
    assert str(URL(iri)) == uri


# RFC 3987 section 3.2: converting URIs back to IRIs.
def test_uri_to_iri() -> None:
    url = URL("http://xn--rsum-bpad.example.org/D%C3%BCrst?q=%C3%A9#%C3%A9")
    assert url.host == "résumé.example.org"
    assert url.path == "/Dürst"
    assert url.query_string == "q=é"
    assert url.fragment == "é"
    assert url.human_repr() == "http://résumé.example.org/Dürst?q=é#é"


# RFC 3492 section 7.1 sample strings.  The samples mix case; hosts are
# lowercased by the UTS #46 mapping, which does not change the encoded
# deltas since only basic code points are affected.
PUNYCODE_SAMPLES = [
    pytest.param(
        "他们为什么不说中文",
        "ihqwcrb4cv8a8dqg056pqjye",
        id="B-chinese-simplified",
    ),
    pytest.param(
        "Pročprostěnemluvíčesky",
        "proprostnemluvesky-uyb24dma41a",
        id="D-czech",
    ),
    pytest.param(
        "למההםפשוטלאמדבריםעברית",
        "4dbcagdahymbxekheh6e0a7fei0b",
        id="E-hebrew",
    ),
    pytest.param(
        "なぜみんな日本語を話してくれないのか",
        "n8jok5ay5dzabd5bym9f0cm5685rrjetr6pdxa",
        id="G-japanese",
    ),
    pytest.param(
        "почемужеонинеговорятпорусски",
        "b1abfaaepdrnnbgefbadotcwatmq2g4l",
        id="I-russian",
    ),
    pytest.param(
        "PorquénopuedensimplementehablarenEspañol",
        "porqunopuedensimplementehablarenespaol-fmd56a",
        id="J-spanish",
    ),
    pytest.param(
        "TạisaohọkhôngthểchỉnóitiếngViệt",
        "tisaohkhngthchnitingvit-kjcr8268qyxafd2f1b9g",
        id="K-vietnamese",
    ),
    pytest.param(
        "3年B組金八先生",
        "3b-ww4c5e180e575a65lsy2b",
        id="L-japanese-mixed",
    ),
    pytest.param(
        "安室奈美恵-with-SUPER-MONKEYS",
        "-with-super-monkeys-pc58ag80a8qai00g7n9n",
        id="M-japanese-mixed",
    ),
    pytest.param(
        "Hello-Another-Way-それぞれの場所",
        "hello-another-way--fc4qua05auwb3674vfr0b",
        id="N-japanese-mixed",
    ),
    pytest.param(
        "ひとつ屋根の下2",
        "2-u9tlzr9756bt3uc0v",
        id="O-japanese-mixed",
    ),
    pytest.param(
        "MajiでKoiする5秒前",
        "majikoi5-783gue6qz075azm5e",
        id="P-japanese-mixed",
    ),
    pytest.param(
        "パフィーdeルンバ",
        "de-jg4avhby1noc0d",
        id="Q-japanese-mixed",
    ),
    pytest.param(
        "そのスピードで",
        "d9juau41awczczp",
        id="R-japanese",
    ),
]


@pytest.mark.parametrize(("label", "punycode"), PUNYCODE_SAMPLES)
def test_punycode_samples(label: str, punycode: str) -> None:
    url = URL.build(scheme="http", host=label)
    assert url.raw_host == f"xn--{punycode}"
    assert URL(f"http://xn--{punycode}/").host == label.lower()


# IDNA2008 keeps deviation characters that IDNA2003 mapped away
# (RFC 5892 and UTS #46 section 6, nontransitional processing).
@pytest.mark.parametrize(
    ("host", "ascii_host"),
    [
        pytest.param("faß.de", "xn--fa-hia.de", id="sharp-s"),
        pytest.param(
            "βόλος.com",
            "xn--nxasmm1c.com",
            id="final-sigma",
        ),
        pytest.param("Bücher.example", "xn--bcher-kva.example", id="uppercase"),
        pytest.param("EXAMPLE.рф", "example.xn--p1ai", id="ascii-label"),
        pytest.param("ÄÖÜ.de", "xn--4ca0bs.de", id="uppercase-only"),
    ],
)
def test_idna2008_uts46_mapping(host: str, ascii_host: str) -> None:
    assert URL.build(scheme="http", host=host).raw_host == ascii_host
    assert URL(f"http://{host}/").raw_host == ascii_host


# RFC 5892 appendix A.2: ZERO WIDTH JOINER is CONTEXTJ and not valid
# between two Latin letters.
def test_contextj_rejected() -> None:
    with pytest.raises(ValueError):
        URL.build(scheme="http", host="a\N{ZERO WIDTH JOINER}b.com")


# RFC 5891 section 5.4: A-labels must decode to valid U-labels.
@pytest.mark.parametrize(
    "host",
    [
        pytest.param(
            "xn--a.com",
            marks=diverges("invalid A-label accepted, .host raises later"),
        ),
        pytest.param(
            "xn--d.tld",
            marks=diverges("invalid A-label accepted, .host raises later"),
        ),
    ],
)
def test_invalid_a_label_rejected(host: str) -> None:
    with pytest.raises(ValueError):
        URL(f"http://{host}/")
