from string import ascii_letters, ascii_lowercase, digits

BASCII_LOWERCASE = ascii_lowercase.encode('ascii')
BPCT_ALLOWED = {'%{:02X}'.format(i).encode('ascii') for i in range(256)}
GEN_DELIMS = ":/?#[]@"
SUB_DELIMS = "!$&'()*+,;="
RESERVED = GEN_DELIMS + SUB_DELIMS
UNRESERVED = ascii_letters + digits + '-._~'
BUNRESERVED = UNRESERVED.encode('ascii')
BUNRESERVED_QUOTED = {'%{:02X}'.format(ord(ch)).encode('ascii'): ord(ch)
                      for ch in UNRESERVED}


def _py_quote(val, *, safe='', plus=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
    val = val.encode('utf8')
    ret = bytearray()
    pct = b''
    safe += UNRESERVED
    bsafe = safe.encode('ascii')
    for ch in val:
        if pct:
            if ch in BASCII_LOWERCASE:
                ch = ch - 32
            pct.append(ch)
            if len(pct) == 3:  # pragma: no branch   # peephole optimizer
                pct = bytes(pct)
                unquoted = BUNRESERVED_QUOTED.get(pct)
                if unquoted:
                    ret.append(unquoted)
                elif pct not in BPCT_ALLOWED:
                    raise ValueError("Unallowed PCT {}".format(pct))
                else:
                    ret.extend(pct)
                pct = b''
            continue
        elif ch == ord('%'):
            pct = bytearray()
            pct.append(ch)
            continue

        if plus:
            if ch == ord(' '):
                ret.append(ord('+'))
                continue
        if ch in bsafe:
            ret.append(ch)
            continue

        ret.extend(('%{:02X}'.format(ch)).encode('ascii'))

    return ret.decode('ascii')


def _py_unquote(val, *, unsafe='', plus=False):
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
                if unquoted in unsafe:
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

        ret.append(ch)

    if pcts:
        try:
            unquoted = pcts.decode('utf8')
        except UnicodeDecodeError:
            ret.append(last_pct)  # %F8
        else:
            if unquoted in unsafe:
                ret.append(_py_quote(unquoted))
            else:
                ret.append(unquoted)
    return ''.join(ret)


try:
    from ._quoting import _quote, _unquote
    quote = _quote
    unquote = _unquote
except ImportError:  # pragma: no cover
    quote = _py_quote
    unquote = _py_unquote
