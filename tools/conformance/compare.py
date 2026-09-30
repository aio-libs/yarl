"""Compare yarl with RFC 3986 and the WHATWG URL Standard.

The WHATWG side comes from the web-platform-tests corpus, pinned to one
commit and verified by checksum; the RFC 3986 side comes from the strict
oracle in rfc3986_oracle.py, which takes IRIs (RFC 3987) as well.  The result is written to REPORT.md next to
this file.  The WPT files are vendored under wpt/, so regenerating and
checking the report never touches the network.

Usage::

    python tools/conformance/compare.py           # regenerate REPORT.md
    python tools/conformance/compare.py --check   # fail if REPORT.md is stale
    python tools/conformance/compare.py --fetch   # download wpt/ at WPT_COMMIT
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import idna
import rfc3986_oracle as rfc

from yarl import URL, Mode

HERE = Path(__file__).resolve().parent
WPT_DIR = HERE / "wpt"
REPORT = HERE / "REPORT.md"

WPT_COMMIT = "c48d58747e1f211527fb695fd60548a997fae617"
WPT_DATE = "2026-09-19"
WPT_FILES = {
    "urltestdata.json": (
        "81e85fd3c199c08ef9c34cf651b3580eeedd080316493bfaf277a6b5ff8cf652"
    ),
    "toascii.json": "644eba9d5b593df8095cfa307222f3014542ff9cc02d555f8e5660059d80470f",
}
WPT_URL = (
    "https://raw.githubusercontent.com/web-platform-tests/wpt/"
    f"{WPT_COMMIT}/url/resources/{{}}"
)

SPECIAL_SCHEMES = frozenset({"http", "https", "ws", "wss", "ftp", "file"})
C0_OR_SPACE = "".join(map(chr, range(0x21)))


def fetch_wpt() -> None:
    """Download the WPT files at WPT_COMMIT and print their checksums."""
    for name in WPT_FILES:
        with urllib.request.urlopen(WPT_URL.format(name), timeout=60) as resp:  # noqa: S310
            data = resp.read()
        (WPT_DIR / name).write_bytes(data)
        print(f"{name}: {hashlib.sha256(data).hexdigest()}")


def load_wpt(name: str) -> list[dict[str, str | None]]:
    path = WPT_DIR / name
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != WPT_FILES[name]:
        sys.exit(f"{path} does not match the checksum pinned in WPT_FILES")
    return [case for case in json.loads(data) if isinstance(case, dict)]


def yarl_outcome(reference: str, base: str | None, mode: Mode) -> str | None:
    """Return the resolved URL, or None when yarl fails or stays relative."""
    try:
        url = URL(reference, mode=mode)
        if base is not None:
            url = URL(base, mode=mode).join(url)
        href = str(url)
    except ValueError:
        return None
    return href if url.scheme else None


def same(first: str | None, second: str | None) -> bool:
    """Compare two outcomes modulo RFC 3986 section 6.2 normalization."""
    if first is None or second is None:
        return first is second
    return first == second or rfc.normalize(first, True) == rfc.normalize(second, True)


@dataclass(frozen=True)
class Case:
    reference: str
    base: str | None
    yarl: str | None  # WHATWG mode, the default
    yarl_rfc: str | None  # RFC 3986 mode
    rfc: str | None
    wpt: str | None

    @property
    def bucket(self) -> str:
        whatwg_ok = same(self.yarl, self.wpt)
        rfc_ok = same(self.yarl_rfc, self.rfc)
        if same(self.wpt, self.rfc):
            return "agree" if whatwg_ok and rfc_ok else "yarl"
        if whatwg_ok and rfc_ok:
            return "both"
        if rfc_ok:
            return "whatwg_mode"
        if whatwg_ok:
            return "rfc_mode"
        return "none"


BUCKETS = {
    "agree": "RFC 3986, WHATWG and yarl in both modes agree",
    "both": "yarl follows each standard in its mode",
    "yarl": "yarl differs, RFC 3986 and WHATWG agree",
    "whatwg_mode": "WHATWG mode differs from WHATWG, RFC mode follows RFC 3986",
    "rfc_mode": "RFC mode differs from RFC 3986, WHATWG mode follows WHATWG",
    "none": "Both modes differ from their standard",
}


def _authority(reference: str) -> str | None:
    rest = re.sub(r"^[A-Za-z][A-Za-z0-9+.\-]*:", "", reference).replace("\\", "/")
    if not rest.startswith("//"):
        return None
    return re.split(r"[/?#]", rest[2:], maxsplit=1)[0]


def _host(authority: str) -> str:
    host = authority.rpartition("@")[2]
    return host if host.startswith("[") else host.partition(":")[0]


CATEGORIES: list[tuple[str, Callable[[str, str | None], bool]]] = [
    (
        "leading or trailing C0 control or space",
        lambda r, b: r != r.strip(C0_OR_SPACE),
    ),
    ("tab or newline inside the input", lambda r, b: any(c in r for c in "\t\n\r")),
    ("backslash", lambda r, b: "\\" in r),
    (
        "IP-literal host",
        lambda r, b: (a := _authority(r)) is not None and _host(a).startswith("["),
    ),
    (
        "numeric host that is not a dotted quad",
        lambda r, b: (
            (a := _authority(r)) is not None
            and re.fullmatch(r"(?:0[xX][0-9A-Fa-f]*|[0-9]+)", _host(a).split(".")[-1])
            is not None
            and rfc.RE_IPV4.fullmatch(_host(a)) is None
        ),
    ),
    (
        "non-ASCII or percent-encoded host",
        lambda r, b: (
            (a := _authority(r)) is not None
            and ("%" in _host(a) or not _host(a).isascii())
        ),
    ),
    ("empty host", lambda r, b: (a := _authority(r)) is not None and not _host(a)),
    ("file scheme", lambda r, b: (r if ":" in r else b or "").startswith("file:")),
    (
        "special scheme without an authority",
        lambda r, b: (
            (m := re.match(r"([A-Za-z][A-Za-z0-9+.\-]*):(?!//)", r)) is not None
            and m.group(1).lower() in SPECIAL_SCHEMES
        ),
    ),
    (
        "characters outside the RFC 3986 grammar",
        lambda r, b: not rfc.is_uri_reference(r),
    ),
    (
        "non-special scheme",
        lambda r, b: (
            (m := re.match(r"([A-Za-z][A-Za-z0-9+.\-]*):", r or b or "")) is not None
            and m.group(1).lower() not in SPECIAL_SCHEMES
        ),
    ),
]


def category(case: Case) -> str:
    for name, matches in CATEGORIES:
        if matches(case.reference, case.base):
            return name
    return "other"


def md(value: str | None, missing: str = "failure") -> str:
    """Format a value as a table-safe Markdown code span."""
    if value is None:
        return f"*{missing}*"
    text = (value if value.isprintable() else repr(value)).replace("|", "\\|")
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def table(header: Iterable[str], rows: Iterable[Iterable[str]]) -> list[str]:
    header = list(header)
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def case_row(case: Case) -> list[str]:
    return [
        md(case.reference),
        md(case.base, "none"),
        md(case.yarl),
        md(case.wpt),
        md(case.yarl_rfc),
        md(case.rfc),
    ]


CASE_HEADER = [
    "Input",
    "Base",
    "yarl WHATWG mode",
    "WHATWG",
    "yarl RFC mode",
    "RFC 3986",
]


def grouped(cases: list[Case]) -> list[str]:
    """Summarize cases by category, then list every case.

    Listing every case keeps moves between sections visible in diffs.
    """
    groups: dict[str, list[Case]] = {}
    for case in cases:
        groups.setdefault(category(case), []).append(case)
    ordered = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    return [
        *table(
            ["Category", "Cases"], ([name, str(len(items))] for name, items in ordered)
        ),
        "",
        *table(
            ["Category", *CASE_HEADER],
            ([name, *case_row(case)] for name, items in ordered for case in items),
        ),
    ]


def toascii_section() -> list[str]:
    rows = []
    total = 0
    for test in load_wpt("toascii.json"):
        total += 1
        source = test["input"]
        assert source is not None
        try:
            got: str | None = URL.build(scheme="http", host=source).raw_host
        except ValueError:
            got = None
        if got != test["output"]:
            rows.append([md(source), md(test["output"]), md(got)])
    return [
        f"`URL.build(host=...)` matches {total - len(rows)} of {total} cases "
        f"with idna {idna.__version__}.",
        "",
        *table(["Input", "WHATWG", "yarl"], rows),
    ]


STANDARDS = """\
| Document | Subject | Status |
|---|---|---|
| RFC 3986 | URI generic syntax | Internet Standard (STD 66); updated by RFC 8820 |
| RFC 9110 section 4.2 | http and https schemes | Internet Standard (STD 97) |
| RFC 3987 | Internationalized Resource Identifiers | Proposed Standard |
| RFC 5891, RFC 5892 | IDNA2008 | Proposed Standard |
| RFC 5895 | Mapping characters for IDNA2008 | Informational |
| RFC 3492 | Punycode | Proposed Standard |
| RFC 5952 | IPv6 address text representation | Proposed Standard |
| RFC 8089 | file scheme | Proposed Standard |
| RFC 6068 | mailto scheme | Proposed Standard |
| RFC 6455 section 3 | ws and wss schemes | Proposed Standard |
| RFC 9844 | IPv6 zone identifiers in user interfaces | Proposed Standard; obsoletes RFC 6874 |
| RFC 6874 | IPv6 zone identifiers in URIs | Obsolete |
| RFC 1808, RFC 2396, RFC 2732 | Earlier URI syntax | Obsolete, replaced by RFC 3986 |
| RFC 3490 | IDNA2003 | Obsolete, replaced by IDNA2008 |
| draft-ietf-6man-rfc6874bis | Zone identifiers, revised | Dead draft, superseded by RFC 9844 |
| draft-ietf-iri-3987bis | IRIs, revised | Dead draft |
| WHATWG URL Standard | URL parsing in browsers | Living Standard, uses UTS #46 for hosts |
"""


def render() -> str:
    cases = [
        Case(
            reference=(ref := test["input"] or ""),
            base=test.get("base"),
            yarl=yarl_outcome(ref, test.get("base"), Mode.WHATWG),
            yarl_rfc=yarl_outcome(ref, test.get("base"), Mode.RFC),
            rfc=rfc.outcome(ref, test.get("base")),
            wpt=None if test.get("failure") else test["href"],
        )
        for test in load_wpt("urltestdata.json")
    ]
    by_bucket: dict[str, list[Case]] = {key: [] for key in BUCKETS}
    for case in cases:
        by_bucket[case.bucket].append(case)
    pairs = Counter[str]()
    for case in cases:
        pairs["yarl WHATWG mode vs WHATWG"] += not same(case.yarl, case.wpt)
        pairs["yarl RFC mode vs RFC 3986"] += not same(case.yarl_rfc, case.rfc)
        pairs["WHATWG vs RFC 3986"] += not same(case.wpt, case.rfc)

    lines = [
        "# yarl conformance report",
        "",
        "<!-- Generated by tools/conformance/compare.py; do not edit by hand. -->",
        "",
        "How yarl compares with RFC 3986 and with the WHATWG URL Standard, "
        "over the web-platform-tests URL corpus "
        f"([`{WPT_COMMIT[:12]}`](https://github.com/web-platform-tests/wpt/tree/"
        f"{WPT_COMMIT}/url/resources), {WPT_DATE}).",
        "",
        "* **yarl**: `URL(input, mode=mode)`, or `URL(base, mode=mode)"
        ".join(URL(input, mode=mode))` when the case has a base, once in the "
        "default WHATWG mode and once in RFC 3986 mode; a result without a "
        "scheme counts as a failure.",
        "* **RFC 3986**: the strict oracle in `rfc3986_oracle.py`, with no "
        "input preprocessing. It takes IRIs too and maps them to URIs as "
        "RFC 3987 section 3.1 does: a non-ASCII host with the RFC 5895 "
        "mapping and IDNA2008, other non-ASCII characters percent-encoded.",
        "* **WHATWG**: the expected `href` from `urltestdata.json`.",
        "",
        "Outcomes that are equal after RFC 3986 section 6.2 normalization "
        "count as agreeing. Known deviations of yarl from the RFCs are "
        "listed as strict xfails in `tests/test_rfc*.py`.",
        "",
        "The goal is that every case is in one of the first two sections: "
        "where the standards agree, yarl agrees with them in both modes; "
        "where they differ, WHATWG mode follows WHATWG and RFC 3986 mode "
        "follows RFC 3986.",
        "",
        "## Standards",
        "",
        STANDARDS,
        "## Summary",
        "",
        *table(
            ["Outcome", "Cases"],
            ([label, str(len(by_bucket[key]))] for key, label in BUCKETS.items()),
        ),
        f"| Total | {len(cases)} |",
        "",
        *table(["Pair", "Disagreements"], ([k, str(v)] for k, v in pairs.items())),
        "",
        f"## yarl differs, RFC 3986 and WHATWG agree ({len(by_bucket['yarl'])})",
        "",
        "Every case where the standards agree and yarl, in either mode, does "
        "not. A change must not add rows here; see AGENTS.md.",
        "",
        *table(CASE_HEADER, map(case_row, by_bucket["yarl"])),
    ]
    for key in ("whatwg_mode", "rfc_mode", "none", "both"):
        lines += [
            "",
            f"## {BUCKETS[key]} ({len(by_bucket[key])})",
            "",
            *grouped(by_bucket[key]),
        ]
    lines += ["", "## IDNA: WHATWG toascii.json", "", *toascii_section(), ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="fail if REPORT.md is out of date"
    )
    mode.add_argument(
        "--fetch", action="store_true", help="download the WPT files at WPT_COMMIT"
    )
    args = parser.parse_args()
    if args.fetch:
        fetch_wpt()
        return
    text = render()
    if not args.check:
        REPORT.write_text(text, encoding="utf-8")
    elif REPORT.read_text(encoding="utf-8") != text:
        sys.exit(f"{REPORT} is out of date; run {Path(__file__).name}")


if __name__ == "__main__":
    main()
