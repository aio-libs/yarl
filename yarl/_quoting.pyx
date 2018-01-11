# cython: language_level=3

import warnings

cdef extern from "Python.h":
    object PyUnicode_New(Py_ssize_t size, Py_UCS4 maxchar)
    Py_ssize_t PyUnicode_CopyCharacters(object to, Py_ssize_t to_start,
                                        object from_, Py_ssize_t from_start,
                                        Py_ssize_t how_many)
    Py_UCS4 PyUnicode_ReadChar(object u, Py_ssize_t index)
    void PyUnicode_WriteChar(object u, Py_ssize_t index, Py_UCS4 value)
    object PyUnicode_Substring(object u, Py_ssize_t start, Py_ssize_t end)

from libc.stdint cimport uint8_t, uint64_t

from string import ascii_letters, digits

cdef str GEN_DELIMS = ":/?#[]@"
cdef str SUB_DELIMS_WITHOUT_QS = "!$'()*,"
cdef str SUB_DELIMS = SUB_DELIMS_WITHOUT_QS + '+?=;'
cdef str RESERVED = GEN_DELIMS + SUB_DELIMS
cdef str UNRESERVED = ascii_letters + digits + '-._~'
cdef str ALLOWED = UNRESERVED + SUB_DELIMS_WITHOUT_QS


cdef inline Py_UCS4 _to_hex(uint8_t v):
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


cdef inline str _make_str(str val, Py_ssize_t val_len, int idx):
    cdef str ret = PyUnicode_New(val_len*3*4 + 1, 1114111)
    if idx != 0:
        PyUnicode_CopyCharacters(ret, 0, val, 0, idx)
    return ret


def _quote(val, *, str safe='', str protected='', bint qs=False, strict=None):
    if strict is not None:  # pragma: no cover
        warnings.warn("strict parameter is ignored")
    if val is None:
        return None
    if type(val) is not str:
        if isinstance(val, str):
            # derived from str
            val = str(val)
        else:
            raise TypeError("Argument should be str")
    return _do_quote(<str>val, safe, protected, qs)


cdef str _do_quote(str val, str safe, str protected, bint qs):
    cdef uint8_t b
    cdef Py_UCS4 ch, unquoted
    cdef str tmp
    cdef Py_ssize_t i
    cdef Py_ssize_t val_len = len(val)
    if val_len == 0:
        return val
    # UTF8 may take up to 4 bytes per symbol
    # every byte is encoded as %XX -- 3 bytes
    cdef object ret = None
    cdef Py_ssize_t ret_idx = 0
    cdef int has_pct = 0
    cdef Py_UCS4 pct[2]
    cdef Py_UCS4 pct2[2]
    cdef int digit1, digit2
    safe += ALLOWED
    if not qs:
        safe += '+&=;'
    safe += protected
    cdef int idx = 0
    while idx < val_len:
        ch = PyUnicode_ReadChar(val, idx)
        idx += 1

        if has_pct:
            pct[has_pct-1] = ch
            has_pct += 1
            if has_pct == 3:
                digit1 = _from_hex(pct[0])
                digit2 = _from_hex(pct[1])
                if digit1 == -1 or digit2 == -1:
                    if ret is None:
                        ret = _make_str(val, val_len, idx)
                    PyUnicode_WriteChar(ret, ret_idx, '%')
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx, '2')
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx, '5')
                    ret_idx += 1
                    idx -= 2
                    has_pct = 0
                    continue

                ch = <Py_UCS4>(digit1 << 4 | digit2)
                has_pct = 0

                if ch in protected:
                    if ret is None:
                        ret = _make_str(val, val_len, idx)
                    PyUnicode_WriteChar(ret, ret_idx, '%')
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx,
                                        _to_hex(<uint8_t>ch >> 4))
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx,
                                        _to_hex(<uint8_t>ch & 0x0f))
                    ret_idx += 1
                elif ch in safe:
                    if ret is None:
                        ret = _make_str(val, val_len, idx)
                    PyUnicode_WriteChar(ret, ret_idx, ch)
                    ret_idx += 1
                else:
                    pct2[0] = _to_hex(<uint8_t>ch >> 4)
                    pct2[1] = _to_hex(<uint8_t>ch & 0x0f)
                    if ret is None:
                        if pct[0] == pct2[0] and pct[1] == pct2[1]:
                            # fast path
                            continue
                        else:
                            ret = _make_str(val, val_len, idx)
                    PyUnicode_WriteChar(ret, ret_idx, '%')
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx, pct2[0])
                    ret_idx += 1
                    PyUnicode_WriteChar(ret, ret_idx, pct2[1])
                    ret_idx += 1

            # special case, if we have only one char after "%"
            elif has_pct == 2 and idx == val_len:
                if ret is None:
                    ret = _make_str(val, val_len, idx)
                PyUnicode_WriteChar(ret, ret_idx, '%')
                ret_idx += 1
                PyUnicode_WriteChar(ret, ret_idx, '2')
                ret_idx += 1
                PyUnicode_WriteChar(ret, ret_idx, '5')
                ret_idx += 1

                idx -= 1
                has_pct = 0

            continue

        elif ch == '%':
            has_pct = 1

            # special case if "%" is last char
            if idx == val_len:
                if ret is None:
                    ret = _make_str(val, val_len, idx)

                PyUnicode_WriteChar(ret, ret_idx, '%')
                ret_idx += 1
                PyUnicode_WriteChar(ret, ret_idx, '2')
                ret_idx += 1
                PyUnicode_WriteChar(ret, ret_idx, '5')
                ret_idx += 1

            continue

        if qs:
            if ch == ' ':
                if ret is None:
                    ret = _make_str(val, val_len, idx)
                PyUnicode_WriteChar(ret, ret_idx, '+')
                ret_idx += 1
                continue
        if ch in safe:
            if ret is not None:
                PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx +=1
            continue
        if ch in ALLOWED:
            if ret is not None:
                PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx +=1
            continue

        if ret is None:
            ret = _make_str(val, val_len, idx)

        ch_bytes = ch.encode("utf-8", errors='ignore')

        for b in ch_bytes:
            PyUnicode_WriteChar(ret, ret_idx, '%')
            ret_idx += 1
            ch = _to_hex(<uint8_t>b >> 4)
            PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx += 1
            ch = _to_hex(<uint8_t>b & 0x0f)
            PyUnicode_WriteChar(ret, ret_idx, ch)
            ret_idx += 1

    if ret is None:
        return val
    else:
        return PyUnicode_Substring(ret, 0, ret_idx)


def _unquote(val, *, unsafe='', qs=False, strict=None):
    if strict is not None:  # pragma: no cover
        warnings.warn("strict parameter is ignored")
    if val is None:
        return None
    if type(val) is not str:
        if isinstance(val, str):
            # derived from str
            val = str(val)
        else:
            raise TypeError("Argument should be str")
    return _do_unquote(<str>val, unsafe, qs)


cdef str _do_unquote(str val, str unsafe='', bint qs=False):
    if len(val) == 0:
        return val
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
                if qs and unquoted in '+=&;':
                    ret.append(_do_quote(unquoted, '', '', True))
                elif unquoted in unsafe:
                    ret.append(_do_quote(unquoted, '', '', False))
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
                ret.append(_do_quote(unquoted, '', '', True))
            elif unquoted in unsafe:
                ret.append(_do_quote(unquoted, '', '', False))
            else:
                ret.append(unquoted)
    return ''.join(ret)
