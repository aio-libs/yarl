# cython: language_level=3

cdef extern from "Python.h":

    char * PyUnicode_AsUTF8AndSize(object s, Py_ssize_t * l)
    object PyUnicode_New(Py_ssize_t size, Py_UCS4 maxchar)
    void PyUnicode_WriteChar(object u, Py_ssize_t index, Py_UCS4 value)
    object PyUnicode_Substring(object u, Py_ssize_t start, Py_ssize_t end)

from libc.stdint cimport uint8_t, uint64_t

from string import ascii_letters, digits

cdef str GEN_DELIMS = ":/?#[]@"
cdef str SUB_DELIMS = "!$&'()*+,;="
cdef str RESERVED = GEN_DELIMS + SUB_DELIMS
cdef str UNRESERVED = ascii_letters + digits + '-._~'

cdef set PCT_ALLOWED = {'%{:02X}'.format(i) for i in range(256)}
cdef dict UNRESERVED_QUOTED = {'%{:02X}'.format(ord(ch)): ord(ch)
                               for ch in UNRESERVED}


cdef inline Py_UCS4 _hex(uint8_t v):
    if v < 10:
        return <Py_UCS4>(v+0x30)  # ord('0') == 0x30
    else:
        return <Py_UCS4>(v+0x41-10)  # ord('A') == 0x41


cdef inline int _from_hex(Py_UCS4 v):
    if '0' <= v <= '9':
        return <int>(v) - 0x30  # ord('0') == 0x30
    elif 'A' <= v <= 'F':
        return <int>(v) - 0x41 + 10  # ord('A') == 0x41
    elif 'a' <= v <= 'f':
        return <int>(v) - 0x61 + 10  # ord('a') == 0x61
    else:
        return -1


def _quote(val, *, str safe='', bint plus=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
    return _do_quote(<str>val, safe, plus)


cdef str _do_quote(str val, str safe, bint plus):
    cdef uint8_t b
    cdef Py_UCS4 ch, unquoted
    cdef str tmp
    cdef char tmpbuf[6]  # place for UTF-8 encoded char plus zero terminator
    cdef Py_ssize_t i, tmpbuf_size
    # UTF8 may take up to 5 bytes per symbol
    # every byte is encoded as %XX -- 3 bytes
    cdef Py_ssize_t ret_size = len(val)*3*5 + 1
    cdef object ret = PyUnicode_New(ret_size, 1114111)
    cdef Py_ssize_t ret_idx = 0
    cdef int has_pct = 0
    cdef Py_UCS4 pct[2]
    cdef int digit1, digit2
    for ch in val:
        if has_pct:
            pct[has_pct-1] = ch
            has_pct += 1
            if has_pct == 3:
                digit1 = _from_hex(pct[0])
                digit2 = _from_hex(pct[1])
                if digit1 == -1 or digit2 == -1:
                    raise ValueError("Unallowed PCT %{}{}".format(pct[0],
                                                                  pct[1]))
                ch = <Py_UCS4>(digit1 << 4 | digit2)
                has_pct = 0

                if ch in UNRESERVED:
                    PyUnicode_WriteChar(ret, ret_idx, ch)
                    ret_idx += 1
                else:
                    PyUnicode_WriteChar(ret, ret_idx, '%')
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx, _hex(<uint8_t>ch >> 4))
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx, _hex(<uint8_t>ch & 0x0f))
                    ret_idx += 1
            continue
        elif ch == '%':
            has_pct = 1
            continue

        if plus:
            if ch == ' ':
                PyUnicode_WriteChar(ret, ret_idx, '+')
                ret_idx += 1
                continue
        if ch in UNRESERVED:
            PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx +=1
            continue
        if ch in safe:
            PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx +=1
            continue

        tmpbuf = PyUnicode_AsUTF8AndSize(ch, &tmpbuf_size)
        for i in range(tmpbuf_size):
            b = tmpbuf[i]
            PyUnicode_WriteChar(ret, ret_idx, '%')
            ret_idx += 1
            ch = _hex(<uint8_t>b >> 4)
            PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx += 1
            ch = _hex(<uint8_t>b & 0x0f)
            PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx += 1

    return PyUnicode_Substring(ret, 0, ret_idx)


def _unquote(val, *, unsafe='', plus=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
    return _do_unquote(<str>val, unsafe, plus)


cdef str _do_unquote(str val, str unsafe='', bint plus=False):
    cdef str pct = ''
    cdef str last_pct = ''
    cdef bytearray pcts = bytearray()
    cdef list ret = []
    cdef str unquoted
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
                    ret.append(_do_quote(unquoted, '', False))
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
                ret.append(_do_quote(unquoted, '', False))
            else:
                ret.append(unquoted)
    return ''.join(ret)
