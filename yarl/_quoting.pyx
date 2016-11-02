# cython: language_level=3

cdef extern from "Python.h":

    char * PyUnicode_AsUTF8AndSize(object s, Py_ssize_t * l)


from string import ascii_letters, digits

cdef str GEN_DELIMS = ":/?#[]@"
cdef str SUB_DELIMS = "!$&'()*+,;="
cdef str RESERVED = GEN_DELIMS + SUB_DELIMS
cdef str UNRESERVED = ascii_letters + digits + '-._~'

cdef set PCT_ALLOWED = {'%{:02X}'.format(i) for i in range(256)}
cdef dict UNRESERVED_QUOTED = {'%{:02X}'.format(ord(ch)): ch
                               for ch in UNRESERVED}


cdef Py_UCS4 _hex(unsigned long v):
    if v < 10:
        return <Py_UCS4>(v+0x30)  # ord('0') == 0x30
    else:
        return <Py_UCS4>(v+0x41-10)  # ord('A') == 0x41


def _quote(val, *, str safe='', bint plus=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
    cdef str _val = <str>val
    cdef list ret = []
    cdef list pct = []
    cdef unsigned char b
    cdef Py_UCS4 ch
    cdef str tmp
    cdef char tmpbuf[5]  # place for UTF-8 encoded char plus zero terminator
    cdef Py_ssize_t i, tmpbuf_size
    for ch in _val:
        if pct:
            if u'a' <= ch <= u'z':
                ch = <Py_UCS4>(<unsigned long>ch - 32)
            pct.append(ch)
            if len(pct) == 3:
                tmp = "".join(pct)
                unquoted = UNRESERVED_QUOTED.get(tmp)
                if unquoted:
                    ret.append(unquoted)
                elif tmp not in PCT_ALLOWED:
                    raise ValueError("Unallowed PCT {}".format(pct))
                else:
                    ret.append(tmp)
                del pct[:]
            continue
        elif ch == u'%':
            pct = [ch]
            continue

        if plus:
            if ch == u' ':
                ret.append(u'+')
                continue
        if ch in UNRESERVED:
            ret.append(ch)
            continue
        if ch in safe:
            ret.append(ch)
            continue

        tmpbuf = PyUnicode_AsUTF8AndSize(ch, &tmpbuf_size)
        for i in range(tmpbuf_size):
            b = tmpbuf[i]
            ret.append('%')
            ret.append(_hex(<unsigned char>b >> 4))
            ret.append(_hex(<unsigned char>b & 0x0f))

    return ''.join(ret)


def _unquote(val, *, unsafe='', plus=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
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
                    ret.append(_quote(unquoted))
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
            ret.append(_quote(unquoted))
        else:
            ret.append(unquoted)
    return ''.join(ret)
