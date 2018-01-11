import warnings
from string import ascii_letters, ascii_lowercase, digits

BASCII_LOWERCASE = ascii_lowercase.encode('ascii')
BPCT_ALLOWED = {'%{:02X}'.format(i).encode('ascii') for i in range(256)}
GEN_DELIMS = ":/?#[]@"
SUB_DELIMS_WITHOUT_QS = "!$'()*,"
SUB_DELIMS = SUB_DELIMS_WITHOUT_QS + '+&=;'
RESERVED = GEN_DELIMS + SUB_DELIMS
UNRESERVED = ascii_letters + digits + '-._~'
ALLOWED = UNRESERVED + SUB_DELIMS_WITHOUT_QS


def _py_quote(val, *, safe='', protected='', qs=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
    val = val.encode('utf8', errors='ignore')
    ret = bytearray()
    pct = b''
    safe += ALLOWED
    if not qs:
        safe += '+&=;'
    safe += protected
    bsafe = safe.encode('ascii')
    idx = 0
    while idx < len(val):
        ch = val[idx]
        idx += 1

        if pct:
            if ch in BASCII_LOWERCASE:
                ch = ch - 32
            pct.append(ch)
            if len(pct) == 3:  # pragma: no branch   # peephole optimizer
                pct = bytes(pct)
                try:
                    unquoted = chr(int(pct[1:].decode('ascii'), base=16))
                except ValueError:
                    ret.extend(b'%25')
                    pct = b''
                    idx -= 2
                    continue

                if unquoted in protected:
                    ret.extend(pct)
                elif unquoted in safe:
                    ret.append(ord(unquoted))
                else:
                    ret.extend(pct)
                pct = b''

            # special case, if we have only one char after "%"
            elif len(pct) == 2 and idx == len(val):
                ret.extend(b'%25')
                pct = b''
                idx -= 1

            continue

        elif ch == ord('%'):
            pct = bytearray()
            pct.append(ch)

            # special case if "%" is last char
            if idx == len(val):
                ret.extend(b'%25')

            continue

        if qs:
            if ch == ord(' '):
                ret.append(ord('+'))
                continue
        if ch in bsafe:
            ret.append(ch)
            continue

        ret.extend(('%{:02X}'.format(ch)).encode('ascii'))

    return ret.decode('ascii')


class _PyQuoter:
    def __init__(self, *, safe='', protected='', qs=False):
        self._safe = safe
        self._protected = protected
        self._qs = qs

    def __call__(self, val):
        return _py_quote(val,
                         safe=self._safe,
                         protected=self._protected,
                         qs=self._qs)


def _py_unquote(val, *, unsafe='', qs=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
    pct = ''
    last_pct = ''
    pcts = bytearray()
    ret = []
    for ch in val:
        if pct:
            pct += ch
            if len(pct) == 3:  # pragma: no branch   # peephole optimizer
                pcts.append(int(pct[1:], base=16))
                last_pct = pct
                pct = ''
            continue
        if pcts:
            try:
                unquoted = pcts.decode('utf8')
            except UnicodeDecodeError:
                pass
            else:
                if qs and unquoted in '+=&;':
                    ret.append(_py_quote(unquoted, qs=True))
                elif unquoted in unsafe:
                    ret.append(_py_quote(unquoted))
                else:
                    ret.append(unquoted)
                del pcts[:]

        if ch == '%':
            pct = ch
            continue

        if pcts:
            ret.append(last_pct)  # %F8ab
            last_pct = ''

        if ch == '+':
            if not qs or ch in unsafe:
                ret.append('+')
            else:
                ret.append(' ')
            continue

        if ch in unsafe:
            ret.append('%')
            h = hex(ord(ch)).upper()[2:]
            for ch in h:
                ret.append(ch)
            continue

        ret.append(ch)

    if pcts:
        try:
            unquoted = pcts.decode('utf8')
        except UnicodeDecodeError:
            ret.append(last_pct)  # %F8
        else:
            if qs and unquoted in '+=&;':
                ret.append(_py_quote(unquoted, qs=True))
            elif unquoted in unsafe:
                ret.append(_py_quote(unquoted))
            else:
                ret.append(unquoted)
    return ''.join(ret)


class _PyUnquoter:
    def __init__(self, *, unsafe='', qs=False):
        self._unsafe = unsafe
        self._qs = qs

    def __call__(self, val):
        return _py_unquote(val, unsafe=self._unsafe, qs=self._qs)


try:
    from ._quoting import _quote, _unquote, _Quoter, _Unquoter
    quote = _quote
    unquote = _unquote
except ImportError:  # pragma: no cover
    quote = _py_quote
    unquote = _py_unquote
    _Quoter = _PyQuoter
    _Unquoter = _PyUnquoter


def quote(val, *, safe='', protected='', qs=False, strict=None):
    if strict is not None:  # pragma: no cover
        warnings.warn("strict parameter is ignored")
    return _Quoter(safe=safe, protected=protected, qs=qs)(val)


def unquote(val, *, unsafe='', qs=False, strict=None):
    if strict is not None:  # pragma: no cover
        warnings.warn("strict parameter is ignored")
    return _Unquoter(unsafe=unsafe, qs=qs)(val)
