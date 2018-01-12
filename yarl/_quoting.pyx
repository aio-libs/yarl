# cython: language_level=3

cdef extern from "Python.h":
    Py_UCS4 PyUnicode_ReadChar(object u, Py_ssize_t index) except -1

from libc.stdint cimport uint8_t, uint64_t
from libc.string cimport memcpy, memset

from cpython.exc cimport PyErr_NoMemory
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython.unicode cimport PyUnicode_DecodeASCII

from string import ascii_letters, digits

cdef str GEN_DELIMS = ":/?#[]@"
cdef str SUB_DELIMS_WITHOUT_QS = "!$'()*,"
cdef str SUB_DELIMS = SUB_DELIMS_WITHOUT_QS + '+?=;'
cdef str RESERVED = GEN_DELIMS + SUB_DELIMS
cdef str UNRESERVED = ascii_letters + digits + '-._~'
cdef str ALLOWED = UNRESERVED + SUB_DELIMS_WITHOUT_QS
cdef str QS = '+&=;'

DEF BUF_SIZE = 8 * 1024  # 8KiB
cdef char BUFFER[BUF_SIZE]


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


cdef inline Py_UCS4 _restore_ch(Py_UCS4 d1, Py_UCS4 d2):
    cdef int digit1 = _from_hex(d1)
    if digit1 < 0:
        return <Py_UCS4>-1
    cdef int digit2 = _from_hex(d2)
    if digit2 < 0:
        return <Py_UCS4>-1
    return <Py_UCS4>(digit1 << 4 | digit2)


cdef uint8_t ALLOWED_TABLE[16]
cdef uint8_t ALLOWED_NOTQS_TABLE[16]


cdef inline bint bit_at(uint8_t array[], uint64_t ch):
    return array[ch >> 3] & (1 << (ch & 7))


cdef inline void set_bit(uint8_t array[], uint64_t ch):
    array[ch >> 3] |= (1 << (ch & 7))


memset(ALLOWED_TABLE, 0, sizeof(ALLOWED_TABLE))
memset(ALLOWED_NOTQS_TABLE, 0, sizeof(ALLOWED_NOTQS_TABLE))

for i in range(128):
    if chr(i) in ALLOWED:
        set_bit(ALLOWED_TABLE, i)
        set_bit(ALLOWED_NOTQS_TABLE, i)
    if chr(i) in QS:
        set_bit(ALLOWED_NOTQS_TABLE, i)

# ----------------- writer ---------------------------

cdef struct Writer:
    char *buf
    Py_ssize_t size
    Py_ssize_t pos
    bint changed


cdef inline void _init_writer(Writer* writer):
    writer.buf = &BUFFER[0]
    writer.size = BUF_SIZE
    writer.pos = 0
    writer.changed = 0


cdef inline void _release_writer(Writer* writer):
    if writer.buf != BUFFER:
        PyMem_Free(writer.buf)


cdef inline int _write_char(Writer* writer, Py_UCS4 ch, bint changed):
    cdef char * buf
    cdef Py_ssize_t size

    if writer.pos == writer.size:
        # reallocate
        size = writer.size * 2
        if writer.buf == BUFFER:
            buf = <char*>PyMem_Malloc(size)
            if buf == NULL:
                PyErr_NoMemory()
                return -1
            memcpy(buf, writer.buf, writer.size)
        else:
            buf = <char*>PyMem_Realloc(writer.buf, size)
            if buf == NULL:
                PyErr_NoMemory()
                return -1
        writer.buf = buf
        writer.size = size
    writer.buf[writer.pos] = <char>ch
    writer.pos += 1
    writer.changed |= changed
    return 0


cdef inline int _write_pct(Writer* writer, uint8_t ch, bint changed):
    if _write_char(writer, '%', changed) < 0:
        return -1
    if _write_char(writer, _to_hex(<uint8_t>ch >> 4), changed) < 0:
        return -1
    return _write_char(writer, _to_hex(<uint8_t>ch & 0x0f), changed)


cdef inline int _write_percent(Writer* writer):
    if _write_char(writer, '%', True) < 0:
        return -1
    if _write_char(writer, '2', True) < 0:
        return -1
    return _write_char(writer, '5', True)


cdef inline int _write_pct_check(Writer* writer, Py_UCS4 ch, Py_UCS4 pct[]):
    cdef Py_UCS4 pct1 = _to_hex(<uint8_t>ch >> 4)
    cdef Py_UCS4 pct2 = _to_hex(<uint8_t>ch & 0x0f)
    cdef bint changed = pct[0] != pct1 or pct[1] != pct2

    if _write_char(writer, '%', changed) < 0:
        return -1
    if _write_char(writer, pct1, changed) < 0:
        return -1
    return _write_char(writer, pct2, changed)


cdef inline int _write_utf8(Writer* writer, Py_UCS4 symbol):
    cdef uint64_t utf = <uint64_t> symbol

    if utf < 0x80:
        return _write_pct(writer, <uint8_t>utf, True)
    elif utf < 0x800:
        if _write_pct(writer, <uint8_t>(0xc0 | (utf >> 6)), True) < 0:
            return -1
        return _write_pct(writer,  <uint8_t>(0x80 | (utf & 0x3f)), True)
    elif 0xD800 <= utf <= 0xDFFF:
        # surogate pair, ignored
        return 0
    elif utf < 0x10000:
        if _write_pct(writer, <uint8_t>(0xe0 | (utf >> 12)), True) < 0:
            return -1
        if _write_pct(writer, <uint8_t>(0x80 | ((utf >> 6) & 0x3f)),
                       True) < 0:
            return -1
        return _write_pct(writer, <uint8_t>(0x80 | (utf & 0x3f)), True)
    elif utf > 0x10FFFF:
        # symbol is too large
        return 0
    else:
        if _write_pct(writer,  <uint8_t>(0xf0 | (utf >> 18)), True) < 0:
            return -1
        if _write_pct(writer,  <uint8_t>(0x80 | ((utf >> 12) & 0x3f)),
                       True) < 0:
           return -1
        if _write_pct(writer,  <uint8_t>(0x80 | ((utf >> 6) & 0x3f)),
                       True) < 0:
            return -1
        return _write_pct(writer, <uint8_t>(0x80 | (utf & 0x3f)), True)


# --------------------- end writer --------------------------


cdef class _Quoter:
    cdef bint _qs

    cdef uint8_t _safe_table[16]
    cdef uint8_t _protected_table[16]

    def __init__(self, *, str safe='', str protected='', bint qs=False):
        cdef Py_UCS4 ch

        self._qs = qs

        if not self._qs:
            memcpy(self._safe_table,
                   ALLOWED_NOTQS_TABLE,
                   sizeof(self._safe_table))
        else:
            memcpy(self._safe_table,
                   ALLOWED_TABLE,
                   sizeof(self._safe_table))
        for ch in safe:
            if ord(ch) > 127:
                raise ValueError("Only safe symbols with ORD < 128 are allowed")
            set_bit(self._safe_table, ch)

        memset(self._protected_table, 0, sizeof(self._protected_table))
        for ch in protected:
            if ord(ch) > 127:
                raise ValueError("Only safe symbols with ORD < 128 are allowed")
            set_bit(self._safe_table, ch)
            set_bit(self._protected_table, ch)

    def __call__(self, val):
        cdef Writer writer
        if val is None:
            return None
        if type(val) is not str:
            if isinstance(val, str):
                # derived from str
                val = str(val)
            else:
                raise TypeError("Argument should be str")
        _init_writer(&writer)
        try:
            return self._do_quote(<str>val, &writer)
        finally:
            _release_writer(&writer)

    cdef str _do_quote(self, str val, Writer *writer):
        cdef Py_UCS4 ch
        cdef Py_ssize_t val_len = len(val)
        if val_len == 0:
            return val
        cdef int has_pct = 0
        cdef Py_UCS4 pct[2]
        cdef int idx = 0

        while idx < val_len:
            ch = PyUnicode_ReadChar(val, idx)
            idx += 1

            if has_pct:
                pct[has_pct-1] = ch
                has_pct += 1
                if has_pct == 3:
                    ch = _restore_ch(pct[0], pct[1])
                    if ch == <Py_UCS4>-1:
                        if _write_percent(writer) < 0:
                            raise
                        idx -= 2
                        has_pct = 0
                        continue

                    has_pct = 0

                    if ch < 128:
                        if bit_at(self._protected_table, ch):
                            if _write_pct(writer, ch, True) < 0:
                                raise
                            continue

                        if bit_at(self._safe_table, ch):
                            if _write_char(writer, ch, True) < 0:
                                raise
                            continue

                    if _write_pct_check(writer, ch, pct) < 0:
                        raise

                # special case, if we have only one char after "%"
                elif has_pct == 2 and idx == val_len:
                    if _write_percent(writer) < 0:
                        raise
                    idx -= 1
                    has_pct = 0

                continue

            elif ch == '%':
                has_pct = 1

                # special case if "%" is last char
                if idx == val_len:
                    if _write_percent(writer) < 0:
                        raise

                continue

            if self._write(writer, ch) < 0:
                raise

        if not writer.changed:
            return val
        else:
            return PyUnicode_DecodeASCII(writer.buf, writer.pos, "strict")

    cdef inline int _write(self, Writer *writer, Py_UCS4 ch):
        if self._qs:
            if ch == ' ':
                return _write_char(writer, '+', True)

        if ch < 128 and bit_at(self._safe_table, ch):
            return _write_char(writer, ch, False)

        return _write_utf8(writer, ch)


cdef class _Unquoter:
    cdef str _unsafe
    cdef bint _qs
    cdef _Quoter _quoter
    cdef _Quoter _qs_quoter

    def __init__(self, *, unsafe='', qs=False):
        self._unsafe = unsafe
        self._qs = qs
        self._quoter = _Quoter()
        self._qs_quoter = _Quoter(qs=True)

    def __call__(self, val):
        if val is None:
            return None
        if type(val) is not str:
            if isinstance(val, str):
                # derived from str
                val = str(val)
            else:
                raise TypeError("Argument should be str")
        return self._do_unquote(<str>val)

    cdef str _do_unquote(self, str val):
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
                    if self._qs and unquoted in '+=&;':
                        ret.append(self._qs_quoter(unquoted))
                    elif unquoted in self._unsafe:
                        ret.append(self._quoter(unquoted))
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
                if not self._qs or ch in self._unsafe:
                    ret.append('+')
                else:
                    ret.append(' ')
                continue

            if ch in self._unsafe:
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
                if self._qs and unquoted in '+=&;':
                    ret.append(self._qs_quoter(unquoted))
                elif unquoted in self._unsafe:
                    ret.append(self._quoter(unquoted))
                else:
                    ret.append(unquoted)
        return ''.join(ret)
