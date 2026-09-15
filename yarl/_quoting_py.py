import re
from string import ascii_letters, ascii_lowercase, digits
from typing import overload

BASCII_LOWERCASE = ascii_lowercase.encode("ascii")
BPCT_ALLOWED = {f"%{i:02X}".encode("ascii") for i in range(256)}
GEN_DELIMS = ":/?#[]@"
SUB_DELIMS_WITHOUT_QS = "!$'()*,"
SUB_DELIMS = SUB_DELIMS_WITHOUT_QS + "+&=;"
RESERVED = GEN_DELIMS + SUB_DELIMS
UNRESERVED = ascii_letters + digits + "-._~"
ALLOWED = UNRESERVED + SUB_DELIMS_WITHOUT_QS


_IS_HEX = re.compile(b"[A-Z0-9][A-Z0-9]")
_HEXDIGITS = "0123456789abcdefABCDEF"
# Every two hex digit escape body, in any case, to the byte it encodes
_PCT_BYTES = {a + b: int(a + b, 16) for a in _HEXDIGITS for b in _HEXDIGITS}
# Strict UTF-8 as accepted by CPython's decoder, see table 3-7 of the Unicode
# standard: lead byte to the sequence length and the range of the second byte.
_UTF8_LEADS = {
    **{lead: (2, 0x80, 0xBF) for lead in range(0xC2, 0xE0)},
    0xE0: (3, 0xA0, 0xBF),
    **{lead: (3, 0x80, 0xBF) for lead in range(0xE1, 0xF0)},
    0xED: (3, 0x80, 0x9F),
    0xF0: (4, 0x90, 0xBF),
    0xF1: (4, 0x80, 0xBF),
    0xF2: (4, 0x80, 0xBF),
    0xF3: (4, 0x80, 0xBF),
    0xF4: (4, 0x80, 0x8F),
}


class _Quoter:
    def __init__(
        self,
        *,
        safe: str = "",
        protected: str = "",
        qs: bool = False,
        requote: bool = True,
    ) -> None:
        if not safe.isascii() or not protected.isascii():
            raise ValueError("Only safe symbols with ORD < 128 are allowed")
        # A safe '%' would be left alone while requoting decodes '%XX', and a
        # safe ' ' would be left alone while qs turns it into '+'
        if requote and ("%" in safe or "%" in protected):
            raise ValueError(
                "safe and protected cannot contain '%' when requote is enabled"
            )
        if qs and (" " in safe or " " in protected):
            raise ValueError("safe and protected cannot contain ' ' when qs is enabled")
        self._safe = safe
        self._protected = protected
        self._qs = qs
        self._requote = requote

    @overload
    def __call__(self, val: str) -> str: ...
    @overload
    def __call__(self, val: None) -> None: ...
    def __call__(self, val: str | None) -> str | None:
        if val is None:
            return None
        if not isinstance(val, str):
            raise TypeError("Argument should be str")
        if not val:
            return ""
        bval = val.encode("utf8", errors="ignore")
        ret = bytearray()
        pct = bytearray()
        safe = self._safe
        safe += ALLOWED
        if not self._qs:
            safe += "+&=;"
        safe += self._protected
        bsafe = safe.encode("ascii")
        idx = 0
        while idx < len(bval):
            ch = bval[idx]
            idx += 1

            if pct:
                if ch in BASCII_LOWERCASE:
                    ch = ch - 32  # convert to uppercase
                pct.append(ch)
                if len(pct) == 3:  # pragma: no branch   # peephole optimizer
                    buf = pct[1:]
                    if not _IS_HEX.match(buf):
                        ret.extend(b"%25")
                        pct.clear()
                        idx -= 2
                        continue
                    try:
                        unquoted = chr(int(pct[1:].decode("ascii"), base=16))
                    except ValueError:
                        ret.extend(b"%25")
                        pct.clear()
                        idx -= 2
                        continue

                    if unquoted in self._protected:
                        ret.extend(pct)
                    elif unquoted in safe:
                        ret.append(ord(unquoted))
                    else:
                        ret.extend(pct)
                    pct.clear()

                # special case, if we have only one char after "%"
                elif len(pct) == 2 and idx == len(bval):
                    ret.extend(b"%25")
                    pct.clear()
                    idx -= 1

                continue

            elif ch == ord("%") and self._requote:
                pct.clear()
                pct.append(ch)

                # special case if "%" is last char
                if idx == len(bval):
                    ret.extend(b"%25")

                continue

            if self._qs and ch == ord(" "):
                ret.append(ord("+"))
                continue
            if ch in bsafe:
                ret.append(ch)
                continue

            ret.extend((f"%{ch:02X}").encode("ascii"))

        ret2 = ret.decode("ascii")
        if ret2 == val:
            return val
        return ret2


class _Unquoter:
    def __init__(
        self,
        *,
        ignore: str = "",
        qs: bool = False,
        plus: bool = False,
    ) -> None:
        # '+' means a space in query strings and in urllib.parse.unquote_plus
        self._plus_is_space = qs or plus
        quoter = _Quoter()
        qs_quoter = _Quoter(qs=True)
        # Decoded characters that are written back percent-encoded
        self._requote = {c: qs_quoter(c) for c in "+=&;"} if qs else {}
        for c in ignore:
            self._requote.setdefault(c, quoter(c))

    @overload
    def __call__(self, val: str) -> str: ...
    @overload
    def __call__(self, val: None) -> None: ...
    def __call__(self, val: str | None) -> str | None:
        if val is None:
            return None
        if not isinstance(val, str):
            raise TypeError("Argument should be str")
        if not val:
            return ""
        if self._plus_is_space and "+" in val:
            val = val.replace("+", " ")
        if (pos := val.find("%")) == -1:
            return val
        requote = self._requote
        ret = []
        # Bytes of an incomplete UTF-8 sequence, their escapes are still in
        # val right before idx
        pending = bytearray()
        need = low = high = 0
        # idx is the end of the part of val already handled; plain runs
        # between '%' characters are appended as a single slice.
        idx = 0
        while pos != -1:
            if pending and pos > idx:
                ret.append(val[idx - len(pending) * 3 : idx])
                pending.clear()
            if pos > idx:
                ret.append(val[idx:pos])
            idx = pos + 1
            if (byte := _PCT_BYTES.get(val[idx : idx + 2])) is not None:
                idx += 2
                if pending:
                    if low <= byte <= high:
                        pending.append(byte)
                        low, high = 0x80, 0xBF
                        if len(pending) == need:
                            unquoted = pending.decode()
                            ret.append(requote.get(unquoted, unquoted))
                            pending.clear()
                        byte = None
                    else:
                        # Not a valid sequence, flush the pending escapes and
                        # start over from this byte
                        ret.append(val[idx - 3 - len(pending) * 3 : idx - 3])
                        pending.clear()
                if byte is None:
                    pass
                elif byte < 0x80:
                    unquoted = chr(byte)
                    ret.append(requote.get(unquoted, unquoted))
                elif byte in _UTF8_LEADS:
                    need, low, high = _UTF8_LEADS[byte]
                    pending.append(byte)
                else:
                    ret.append(val[idx - 3 : idx])
            else:
                # A '%' that does not start an escape is kept as is
                if pending:
                    ret.append(val[idx - 1 - len(pending) * 3 : idx - 1])
                    pending.clear()
                ret.append("%")
            pos = val.find("%", idx)

        if pending:
            ret.append(val[idx - len(pending) * 3 : idx])
        ret.append(val[idx:])

        ret2 = "".join(ret)
        if ret2 == val:
            return val
        return ret2
