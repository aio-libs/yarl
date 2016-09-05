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


def quote(val, *, safe='', plus=False):
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
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


def unquote(val, *, unsafe='', plus=False):
    pct = ''
    pcts = bytearray()
    ret = []
    for ch in val:
        if pct:
            pct += ch
            if len(pct) == 3:  # pragma: no branch   # peephole optimizer
                pcts.append(int(pct[1:], base=16))
                pct = ''
            continue
        if pcts:
            try:
                unquoted = pcts.decode('utf8')
            except UnicodeDecodeError:
                pass
            else:
                if unquoted in unsafe:
                    ret.append(quote(unquoted))
                else:
                    ret.append(unquoted)
                del pcts[:]

        if ch == '%':
            pct = ch
            continue

        ret.append(ch)

    if pcts:
        unquoted = pcts.decode('utf8')
        if unquoted in unsafe:
            ret.append(quote(unquoted))
        else:
            ret.append(unquoted)
    return ''.join(ret)
