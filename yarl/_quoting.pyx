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


def _quote(val, *, str safe='', bint plus=False):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Argument should be str")
    if not val:
        return ''
    cdef str _val = <str>val
    cdef list pct = []
    cdef uint8_t b
    cdef Py_UCS4 ch, unquoted
    cdef str tmp
    cdef char tmpbuf[6]  # place for UTF-8 encoded char plus zero terminator
    cdef Py_ssize_t i, tmpbuf_size
    cdef Py_ssize_t ret_size = len(_val)*6 + 1
    cdef object ret = PyUnicode_New(ret_size, 1114111)
    cdef Py_ssize_t ret_idx = 0
    for ch in _val:
        if pct:
            if u'a' <= ch <= u'z':
                ch = <Py_UCS4>(<uint64_t>ch - 32)
            pct.append(ch)
            if len(pct) == 3:
                tmp = "".join(pct)
                unquoted = UNRESERVED_QUOTED.get(tmp)
                if unquoted:
                    PyUnicode_WriteChar(ret, ret_idx, unquoted)
                    ret_idx += 1
                elif tmp not in PCT_ALLOWED:
                    raise ValueError("Unallowed PCT {}".format(pct))
                else:
                    for i in range(3):
                        PyUnicode_WriteChar(ret, ret_idx, pct[i])
                        ret_idx += 1
                    del pct[:]
            continue
        elif ch == '%':
            pct = ['%']
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

    assert ret_idx < len(ret)
    return PyUnicode_Substring(ret, 0, ret_idx)


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
