from cpython.exc cimport PyErr_NoMemory
from cpython.mem cimport PyMem_Free, PyMem_Malloc, PyMem_Realloc
from cpython.object cimport PyObject
from cpython.tuple cimport PyTuple_GET_ITEM
from cpython.unicode cimport (
    Py_UCS1,
    Py_UCS2,
    PyUnicode_DATA,
    PyUnicode_DecodeASCII,
    PyUnicode_1BYTE_KIND,
    PyUnicode_2BYTE_KIND,
    PyUnicode_4BYTE_KIND,
    PyUnicode_FindChar,
    PyUnicode_FromKindAndData,
    PyUnicode_GET_LENGTH,
    PyUnicode_KIND,
    PyUnicode_READ,
)
from libc.stdint cimport uint8_t, uint64_t
from libc.string cimport memcpy, memset

from string import ascii_letters, digits


cdef str GEN_DELIMS = ":/?#[]@"
cdef str SUB_DELIMS_WITHOUT_QS = "!$'()*,"
cdef str SUB_DELIMS = SUB_DELIMS_WITHOUT_QS + '+?=;'
cdef str RESERVED = GEN_DELIMS + SUB_DELIMS
cdef str UNRESERVED = ascii_letters + digits + '-._~'
cdef str ALLOWED = UNRESERVED + SUB_DELIMS_WITHOUT_QS
cdef str QS = '+&=;'

DEF BUF_SIZE = 8 * 1024  # 8KiB
DEF UCS4_BUF_SIZE = 256

DEF ASCII_LIMIT = 0x80  # code points below this are ASCII
# Bitmaps with one bit per ASCII character
DEF BYTE_BITS_SHIFT = 3  # log2 of the 8 bits in a byte
DEF BYTE_BIT_MASK = 7
DEF ASCII_TABLE_SIZE = ASCII_LIMIT >> BYTE_BITS_SHIFT
DEF HEX_DIGIT_BITS = 4
DEF HEX_DIGIT_MASK = 0x0F
DEF HEX_LETTER_VALUE = 10  # value of the hex digit A
DEF PCT_HEX_LEN = 2  # the XX in %XX
DEF PCT_ESCAPE_LEN = 3  # %XX

# UTF-8, see table 3-7 of the Unicode standard. The decoder is as strict as
# CPython's.
DEF UTF8_MAX_BYTES = 4
DEF UTF8_2BYTE_LIMIT = 0x800  # code points below these limits use 2, 3 bytes
DEF UTF8_3BYTE_LIMIT = 0x10000
DEF MAX_CODE_POINT = 0x10FFFF
DEF SURROGATE_MIN = 0xD800
DEF SURROGATE_MAX = 0xDFFF
DEF UTF8_CONT_MARKER = 0x80  # 10xxxxxx
DEF UTF8_LEAD2_MARKER = 0xC0  # 110xxxxx
DEF UTF8_LEAD3_MARKER = 0xE0  # 1110xxxx
DEF UTF8_LEAD4_MARKER = 0xF0  # 11110xxx
DEF UTF8_CONT_MIN = 0x80  # continuation bytes are 10xxxxxx
DEF UTF8_CONT_MAX = 0xBF
DEF UTF8_CONT_PAYLOAD = 0x3F
DEF UTF8_CONT_BITS = 6
DEF UTF8_LEAD2_MIN = 0xC2  # 0xC0 and 0xC1 only start overlong encodings
DEF UTF8_LEAD2_MAX = 0xDF
DEF UTF8_LEAD2_PAYLOAD = 0x1F
DEF UTF8_LEAD3_MIN = 0xE0
DEF UTF8_LEAD3_MAX = 0xEF
DEF UTF8_LEAD3_PAYLOAD = 0x0F
DEF UTF8_LEAD4_MIN = 0xF0
DEF UTF8_LEAD4_MAX = 0xF4  # higher lead bytes encode past U+10FFFF
DEF UTF8_LEAD4_PAYLOAD = 0x07
# Lead bytes that narrow the range of the byte right after them
DEF UTF8_LEAD_E0 = 0xE0
DEF UTF8_E0_CONT_MIN = 0xA0  # E0 80..9F would be overlong
DEF UTF8_LEAD_ED = 0xED
DEF UTF8_ED_CONT_MAX = 0x9F  # ED A0..BF would be a surrogate
DEF UTF8_LEAD_F0 = 0xF0
DEF UTF8_F0_CONT_MIN = 0x90  # F0 80..8F would be overlong
DEF UTF8_LEAD_F4 = 0xF4
DEF UTF8_F4_CONT_MAX = 0x8F  # F4 90..BF would be past U+10FFFF


cdef inline Py_UCS4 _to_hex(uint8_t v) noexcept:
    if v < HEX_LETTER_VALUE:
        return <Py_UCS4>(v + ord('0'))
    return <Py_UCS4>(v - HEX_LETTER_VALUE + ord('A'))


cdef inline int _from_hex(Py_UCS4 v) noexcept:
    if '0' <= v <= '9':
        return <int>v - ord('0')
    if 'A' <= v <= 'F':
        return <int>v - ord('A') + HEX_LETTER_VALUE
    if 'a' <= v <= 'f':
        return <int>v - ord('a') + HEX_LETTER_VALUE
    return -1


cdef inline int _is_lower_hex(Py_UCS4 v) noexcept:
    return 'a' <= v <= 'f'


cdef inline bint _is_surrogate(Py_UCS4 ch) noexcept:
    return SURROGATE_MIN <= ch <= SURROGATE_MAX


cdef inline Py_ssize_t _skip_surrogates(
    int kind, const void *data, Py_ssize_t idx, Py_ssize_t length
) noexcept:
    # Advance past lone surrogates; they cannot be UTF-8 encoded and are
    # dropped, so they must not break up a percent escape during requoting.
    while idx < length and _is_surrogate(PyUnicode_READ(kind, data, idx)):
        idx += 1
    return idx


cdef inline long _restore_ch(Py_UCS4 d1, Py_UCS4 d2) noexcept:
    cdef int digit1 = _from_hex(d1)
    if digit1 < 0:
        return -1
    cdef int digit2 = _from_hex(d2)
    if digit2 < 0:
        return -1
    return digit1 << HEX_DIGIT_BITS | digit2


cdef uint8_t ALLOWED_TABLE[ASCII_TABLE_SIZE]
cdef uint8_t ALLOWED_NOTQS_TABLE[ASCII_TABLE_SIZE]


cdef inline bint bit_at(uint8_t array[], uint64_t ch) noexcept:
    return array[ch >> BYTE_BITS_SHIFT] & (1 << (ch & BYTE_BIT_MASK))


cdef inline void set_bit(uint8_t array[], uint64_t ch) noexcept:
    array[ch >> BYTE_BITS_SHIFT] |= (1 << (ch & BYTE_BIT_MASK))


memset(ALLOWED_TABLE, 0, sizeof(ALLOWED_TABLE))
memset(ALLOWED_NOTQS_TABLE, 0, sizeof(ALLOWED_NOTQS_TABLE))

for i in range(ASCII_LIMIT):
    if chr(i) in ALLOWED:
        set_bit(ALLOWED_TABLE, i)
        set_bit(ALLOWED_NOTQS_TABLE, i)
    if chr(i) in QS:
        set_bit(ALLOWED_NOTQS_TABLE, i)

# ----------------- writer ---------------------------

cdef struct Writer:
    char *buf
    bint heap_allocated_buf
    Py_ssize_t size
    Py_ssize_t pos
    bint changed


cdef inline void _init_writer(Writer* writer, char* buf):
    writer.buf = buf
    writer.heap_allocated_buf = False
    writer.size = BUF_SIZE
    writer.pos = 0
    writer.changed = 0


cdef inline void _release_writer(Writer* writer):
    if writer.heap_allocated_buf:
        PyMem_Free(writer.buf)


cdef inline int _write_char(Writer* writer, Py_UCS4 ch, bint changed):
    cdef char * buf
    cdef Py_ssize_t size

    if writer.pos == writer.size:
        # reallocate
        size = writer.size + BUF_SIZE
        if not writer.heap_allocated_buf:
            buf = <char*>PyMem_Malloc(size)
            if buf == NULL:
                PyErr_NoMemory()
                return -1
            memcpy(buf, writer.buf, writer.size)
            writer.heap_allocated_buf = True
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
    if _write_char(writer, _to_hex(<uint8_t>ch >> HEX_DIGIT_BITS), changed) < 0:
        return -1
    return _write_char(writer, _to_hex(<uint8_t>ch & HEX_DIGIT_MASK), changed)


cdef inline int _write_utf8(Writer* writer, Py_UCS4 symbol):
    cdef uint64_t utf = <uint64_t> symbol

    if utf < ASCII_LIMIT:
        return _write_pct(writer, <uint8_t>utf, True)
    if utf < UTF8_2BYTE_LIMIT:
        if _write_pct(
            writer, <uint8_t>(UTF8_LEAD2_MARKER | (utf >> UTF8_CONT_BITS)), True
        ) < 0:
            return -1
        return _write_pct(
            writer, <uint8_t>(UTF8_CONT_MARKER | (utf & UTF8_CONT_PAYLOAD)), True
        )
    if _is_surrogate(symbol):
        # lone surrogate; invalid in UTF-8 so it is dropped, matching the
        # pure-Python quoter's errors="ignore" encode. Mark the writer as
        # changed so _do_quote returns the surrogate-free buffer rather than
        # the untouched input string.
        writer.changed = True
        return 0
    if utf < UTF8_3BYTE_LIMIT:
        if _write_pct(
            writer, <uint8_t>(UTF8_LEAD3_MARKER | (utf >> 2 * UTF8_CONT_BITS)), True
        ) < 0:
            return -1
        if _write_pct(
            writer,
            <uint8_t>(UTF8_CONT_MARKER | ((utf >> UTF8_CONT_BITS) & UTF8_CONT_PAYLOAD)),
            True,
        ) < 0:
            return -1
        return _write_pct(
            writer, <uint8_t>(UTF8_CONT_MARKER | (utf & UTF8_CONT_PAYLOAD)), True
        )
    if utf > MAX_CODE_POINT:
        # symbol is too large
        return 0
    if _write_pct(
        writer, <uint8_t>(UTF8_LEAD4_MARKER | (utf >> 3 * UTF8_CONT_BITS)), True
    ) < 0:
        return -1
    if _write_pct(
        writer,
        <uint8_t>(
            UTF8_CONT_MARKER | ((utf >> 2 * UTF8_CONT_BITS) & UTF8_CONT_PAYLOAD)
        ),
        True,
    ) < 0:
        return -1
    if _write_pct(
        writer,
        <uint8_t>(UTF8_CONT_MARKER | ((utf >> UTF8_CONT_BITS) & UTF8_CONT_PAYLOAD)),
        True,
    ) < 0:
        return -1
    return _write_pct(
        writer, <uint8_t>(UTF8_CONT_MARKER | (utf & UTF8_CONT_PAYLOAD)), True
    )


# --------------------- end writer --------------------------


cdef class _Quoter:
    cdef bint _qs
    cdef bint _requote

    cdef uint8_t _safe_table[ASCII_TABLE_SIZE]
    cdef uint8_t _protected_table[ASCII_TABLE_SIZE]

    def __init__(
            self, *, str safe='', str protected='', bint qs=False, bint requote=True,
    ):
        cdef Py_UCS4 ch

        self._qs = qs
        self._requote = requote

        if not self._qs:
            memcpy(self._safe_table,
                   ALLOWED_NOTQS_TABLE,
                   sizeof(self._safe_table))
        else:
            memcpy(self._safe_table,
                   ALLOWED_TABLE,
                   sizeof(self._safe_table))
        for ch in safe:
            if ord(ch) >= ASCII_LIMIT:
                raise ValueError("Only safe symbols with ORD < 128 are allowed")
            set_bit(self._safe_table, ch)

        memset(self._protected_table, 0, sizeof(self._protected_table))
        for ch in protected:
            if ord(ch) >= ASCII_LIMIT:
                raise ValueError("Only safe symbols with ORD < 128 are allowed")
            set_bit(self._safe_table, ch)
            set_bit(self._protected_table, ch)

    def __call__(self, val):
        if val is None:
            return None
        if type(val) is not str:
            if not isinstance(val, str):
                raise TypeError("Argument should be str")
            # derived from str
            val = str(val)
        return self._do_quote_or_skip(<str>val)

    cdef str _do_quote_or_skip(self, str val):
        cdef char[BUF_SIZE] buffer
        cdef Py_UCS4 ch
        cdef Py_ssize_t length = PyUnicode_GET_LENGTH(val)
        cdef Py_ssize_t idx = length
        cdef bint must_quote = 0
        cdef Writer writer
        cdef int kind = PyUnicode_KIND(val)
        cdef const void *data = PyUnicode_DATA(val)

        # If everything in the string is in the safe
        # table and all ASCII, we can skip quoting
        while idx:
            idx -= 1
            ch = PyUnicode_READ(kind, data, idx)
            if ch >= ASCII_LIMIT or not bit_at(self._safe_table, ch):
                must_quote = 1
                break

        if not must_quote:
            return val

        _init_writer(&writer, &buffer[0])
        try:
            return self._do_quote(<str>val, length, kind, data, &writer)
        finally:
            _release_writer(&writer)

    cdef str _do_quote(
        self,
        str val,
        Py_ssize_t length,
        int kind,
        const void *data,
        Writer *writer
    ):
        cdef Py_UCS4 ch
        cdef Py_UCS4 d1
        cdef Py_UCS4 d2
        cdef long chl
        cdef int changed
        cdef bint surrogate_skipped
        cdef Py_ssize_t idx = 0
        cdef Py_ssize_t pos1
        cdef Py_ssize_t pos2

        while idx < length:
            ch = PyUnicode_READ(kind, data, idx)
            idx += 1
            if ch == '%' and self._requote and idx < length:
                # Lone surrogates are dropped (see _skip_surrogates), so look
                # through them for the two hex digits of the "%XX" escape; this
                # keeps the C quoter consistent with the pure-Python backend,
                # which strips surrogates before scanning.
                pos1 = _skip_surrogates(kind, data, idx, length)
                pos2 = _skip_surrogates(kind, data, pos1 + 1, length)
                if pos2 < length:
                    d1 = PyUnicode_READ(kind, data, pos1)
                    d2 = PyUnicode_READ(kind, data, pos2)
                    chl = _restore_ch(d1, d2)
                else:
                    chl = -1
                if chl != -1:
                    ch = <Py_UCS4>chl
                    surrogate_skipped = pos1 != idx or pos2 != pos1 + 1
                    idx = pos2 + 1
                    if ch < ASCII_LIMIT:
                        if bit_at(self._protected_table, ch):
                            if _write_pct(writer, ch, True) < 0:
                                raise
                            continue

                        if bit_at(self._safe_table, ch):
                            if _write_char(writer, ch, True) < 0:
                                raise
                            continue

                    changed = (surrogate_skipped or
                               _is_lower_hex(d1) or _is_lower_hex(d2))
                    if _write_pct(writer, ch, changed) < 0:
                        raise
                    continue
                else:
                    ch = '%'

            if self._write(writer, ch) < 0:
                raise

        if not writer.changed:
            return val
        return PyUnicode_DecodeASCII(writer.buf, writer.pos, "strict")

    cdef inline int _write(self, Writer *writer, Py_UCS4 ch):
        if self._qs:
            if ch == ' ':
                return _write_char(writer, '+', True)

        if ch < ASCII_LIMIT and bit_at(self._safe_table, ch):
            return _write_char(writer, ch, False)

        return _write_utf8(writer, ch)


cdef inline Py_ssize_t _utf8_sequence_length(uint8_t lead) noexcept:
    if UTF8_LEAD2_MIN <= lead <= UTF8_LEAD2_MAX:
        return 2
    if UTF8_LEAD3_MIN <= lead <= UTF8_LEAD3_MAX:
        return 3
    if UTF8_LEAD4_MIN <= lead <= UTF8_LEAD4_MAX:
        return 4
    return 0


cdef inline bint _utf8_is_continuation(
    uint8_t lead, Py_ssize_t pos, Py_UCS4 byte
) noexcept:
    if pos == 1:
        if lead == UTF8_LEAD_E0:
            return UTF8_E0_CONT_MIN <= byte <= UTF8_CONT_MAX
        if lead == UTF8_LEAD_ED:
            return UTF8_CONT_MIN <= byte <= UTF8_ED_CONT_MAX
        if lead == UTF8_LEAD_F0:
            return UTF8_F0_CONT_MIN <= byte <= UTF8_CONT_MAX
        if lead == UTF8_LEAD_F4:
            return UTF8_CONT_MIN <= byte <= UTF8_F4_CONT_MAX
    return UTF8_CONT_MIN <= byte <= UTF8_CONT_MAX


cdef inline Py_UCS4 _utf8_decode(const uint8_t *buf, Py_ssize_t length) noexcept:
    if length == 2:
        return (
            (buf[0] & UTF8_LEAD2_PAYLOAD) << UTF8_CONT_BITS
            | (buf[1] & UTF8_CONT_PAYLOAD)
        )
    if length == 3:
        return (
            (buf[0] & UTF8_LEAD3_PAYLOAD) << 2 * UTF8_CONT_BITS
            | (buf[1] & UTF8_CONT_PAYLOAD) << UTF8_CONT_BITS
            | (buf[2] & UTF8_CONT_PAYLOAD)
        )
    return (
        (buf[0] & UTF8_LEAD4_PAYLOAD) << 3 * UTF8_CONT_BITS
        | (buf[1] & UTF8_CONT_PAYLOAD) << 2 * UTF8_CONT_BITS
        | (buf[2] & UTF8_CONT_PAYLOAD) << UTF8_CONT_BITS
        | (buf[3] & UTF8_CONT_PAYLOAD)
    )


# Output buffer for _Unquoter, holding code points instead of bytes.
cdef struct UCS4Writer:
    Py_UCS4 *buf
    bint heap_allocated_buf
    Py_ssize_t size
    Py_ssize_t pos


cdef inline void _init_ucs4_writer(UCS4Writer* writer, Py_UCS4* buf) noexcept:
    writer.buf = buf
    writer.heap_allocated_buf = False
    writer.size = UCS4_BUF_SIZE
    writer.pos = 0


cdef inline void _release_ucs4_writer(UCS4Writer* writer) noexcept:
    if writer.heap_allocated_buf:
        PyMem_Free(writer.buf)


cdef inline int _ucs4_reserve(UCS4Writer* writer, Py_ssize_t extra) except -1:
    cdef Py_ssize_t size = writer.pos + extra
    cdef Py_UCS4 *buf
    if size <= writer.size:
        return 0
    if size < writer.size * 2:
        size = writer.size * 2
    if writer.heap_allocated_buf:
        buf = <Py_UCS4*>PyMem_Realloc(writer.buf, size * sizeof(Py_UCS4))
    else:
        buf = <Py_UCS4*>PyMem_Malloc(size * sizeof(Py_UCS4))
        if buf != NULL:
            memcpy(buf, writer.buf, writer.pos * sizeof(Py_UCS4))
    if buf == NULL:
        PyErr_NoMemory()
        return -1
    writer.buf = buf
    writer.heap_allocated_buf = True
    writer.size = size
    return 0


cdef inline int _ucs4_write_char(UCS4Writer* writer, Py_UCS4 ch) except -1:
    if writer.pos == writer.size:
        _ucs4_reserve(writer, 1)
    writer.buf[writer.pos] = ch
    writer.pos += 1
    return 0


ctypedef fused _narrow_ucs:
    Py_UCS1
    Py_UCS2


cdef inline void _widen_to_ucs4(
    Py_UCS4 *out, const _narrow_ucs *src, Py_ssize_t length
) noexcept:
    # No public API copies part of a str into a UCS4 buffer; CPython widens
    # with the same plain loop internally.
    cdef Py_ssize_t i
    for i in range(length):
        out[i] = src[i]


cdef inline int _ucs4_write_slice(
    UCS4Writer* writer,
    int kind,
    const void *data,
    Py_ssize_t start,
    Py_ssize_t end,
) except -1:
    cdef Py_ssize_t length = end - start
    cdef Py_UCS4 *out
    if length <= 0:
        return 0
    _ucs4_reserve(writer, length)
    out = writer.buf + writer.pos
    if kind == PyUnicode_1BYTE_KIND:
        _widen_to_ucs4(out, <const Py_UCS1*>data + start, length)
    elif kind == PyUnicode_2BYTE_KIND:
        _widen_to_ucs4(out, <const Py_UCS2*>data + start, length)
    else:
        memcpy(out, <const Py_UCS4*>data + start, length * sizeof(Py_UCS4))
    writer.pos += length
    return 0


cdef inline int _ucs4_write_str(UCS4Writer* writer, str s) except -1:
    return _ucs4_write_slice(
        writer, PyUnicode_KIND(s), PyUnicode_DATA(s), 0, PyUnicode_GET_LENGTH(s)
    )


cdef class _Unquoter:
    cdef str _ignore
    cdef bint _has_non_ascii_ignore
    cdef bint _plus_is_space  # to match urllib.parse.unquote_plus
    # '%' followed by the unsafe characters, except '+' which is never
    # percent-encoded when it appears literally.
    cdef bytes _special
    cdef const unsigned char *_special_char
    cdef Py_ssize_t _special_len
    # What to write for each decoded ASCII character, None to write it as is.
    cdef tuple _requote
    cdef _Quoter _quoter

    def __init__(self, *, ignore="", unsafe="", qs=False, plus=False):
        cdef _Quoter qs_quoter = _Quoter(qs=True)
        self._ignore = ignore
        self._has_non_ascii_ignore = not ignore.isascii()
        self._plus_is_space = (qs or plus) and '+' not in unsafe
        # unsafe may only be ascii characters
        self._special = ('%' + unsafe.replace('+', '')).encode('ascii')
        self._special_char = self._special
        self._special_len = len(self._special)
        self._quoter = _Quoter()
        self._requote = tuple(
            qs_quoter(c) if qs and c in '+=&;'
            else self._quoter(c) if c in unsafe or c in ignore
            else None
            for c in map(chr, range(ASCII_LIMIT))
        )

    def __call__(self, val):
        if val is None:
            return None
        if type(val) is not str:
            if not isinstance(val, str):
                raise TypeError("Argument should be str")
            # derived from str
            val = str(val)
        return self._do_unquote(<str>val)

    cdef str _do_unquote(self, str val):
        cdef Py_ssize_t length = PyUnicode_GET_LENGTH(val)
        if length == 0:
            return val

        # A literal '+' never takes part in an escape sequence, so turning
        # every '+' into a space up front gives the same result as doing it
        # in the loop below.
        if self._plus_is_space and PyUnicode_FindChar(val, '+', 0, length, 1) != -1:
            val = val.replace('+', ' ')
        # Skip straight to the first character that may need rewriting;
        # most strings have none and are returned as is.
        cdef Py_ssize_t idx = self._find_special(val, 0, length)
        if idx == length:
            return val

        cdef Py_UCS4 stack_buf[UCS4_BUF_SIZE]
        cdef UCS4Writer writer
        _init_ucs4_writer(&writer, stack_buf)
        try:
            if length > UCS4_BUF_SIZE:
                # The output is rarely longer than the input
                _ucs4_reserve(&writer, length)
            return self._unquote_from(&writer, val, length, idx)
        finally:
            _release_ucs4_writer(&writer)

    cdef str _unquote_from(
        self, UCS4Writer* writer, str val, Py_ssize_t length, Py_ssize_t idx
    ):
        cdef uint8_t buffer[UTF8_MAX_BYTES]
        cdef Py_ssize_t buflen = 0
        cdef Py_UCS4 ch = 0
        cdef long chl = 0
        cdef Py_ssize_t run_end
        cdef bint changed = 0
        cdef int kind = PyUnicode_KIND(val)
        cdef const void *data = PyUnicode_DATA(val)
        _ucs4_write_slice(writer, kind, data, 0, idx)
        while idx < length:
            ch = PyUnicode_READ(kind, data, idx)
            idx += 1
            if ch == '%' and idx <= length - PCT_HEX_LEN:
                chl = _restore_ch(
                    PyUnicode_READ(kind, data, idx),
                    PyUnicode_READ(kind, data, idx + 1)
                )
                if chl != -1:
                    changed = 1
                    ch = <Py_UCS4>chl
                    idx += PCT_HEX_LEN
                    if buflen:
                        if _utf8_is_continuation(buffer[0], buflen, ch):
                            buffer[buflen] = <uint8_t>ch
                            buflen += 1
                            if buflen == _utf8_sequence_length(buffer[0]):
                                self._write_unquoted(
                                    writer, _utf8_decode(buffer, buflen)
                                )
                                buflen = 0
                            continue
                        # Not a valid sequence, keep the pending escapes as is
                        # and start over from this byte.
                        _ucs4_write_slice(
                            writer,
                            kind,
                            data,
                            idx - PCT_ESCAPE_LEN - buflen * PCT_ESCAPE_LEN,
                            idx - PCT_ESCAPE_LEN,
                        )
                        buflen = 0
                    if ch < ASCII_LIMIT:
                        self._write_unquoted(writer, ch)
                    elif _utf8_sequence_length(<uint8_t>ch):
                        buffer[0] = <uint8_t>ch
                        buflen = 1
                    else:
                        _ucs4_write_slice(
                            writer, kind, data, idx - PCT_ESCAPE_LEN, idx
                        )
                    continue

            if buflen:
                _ucs4_write_slice(
                    writer, kind, data, idx - 1 - buflen * PCT_ESCAPE_LEN, idx - 1
                )
                buflen = 0

            if self._is_literal_unsafe(ch):
                changed = 1
                _ucs4_write_char(writer, '%')
                _ucs4_write_str(writer, hex(ord(ch)).upper()[2:])
                continue

            # Copy everything up to the next character that may need
            # rewriting in one go.
            run_end = self._find_special(val, idx, length)
            _ucs4_write_slice(writer, kind, data, idx - 1, run_end)
            idx = run_end

        if not changed:
            return val

        if buflen:
            _ucs4_write_slice(
                writer, kind, data, length - buflen * PCT_ESCAPE_LEN, length
            )

        return PyUnicode_FromKindAndData(
            PyUnicode_4BYTE_KIND, writer.buf, writer.pos
        )

    cdef inline int _write_unquoted(self, UCS4Writer* writer, Py_UCS4 ch) except -1:
        cdef PyObject *requote
        if ch < ASCII_LIMIT:
            requote = PyTuple_GET_ITEM(self._requote, ch)
            if requote != <PyObject*>None:
                return _ucs4_write_str(writer, <str>requote)
        elif self._has_non_ascii_ignore and ch in self._ignore:
            return _ucs4_write_str(writer, self._quoter(chr(ch)))
        return _ucs4_write_char(writer, ch)

    cdef inline Py_ssize_t _find_special(
        self, str val, Py_ssize_t start, Py_ssize_t end
    ) except -1:
        """Return the index of the next '%' or unsafe character, or end."""
        cdef Py_ssize_t found
        cdef Py_ssize_t i
        # Each search looks for a single character, so a hit cannot return
        # right away; the search for another character may still find an
        # earlier match. Narrowing end limits those searches to before the hit.
        # For the unquoters in _quoters.py this is only the search for '%'.
        for i in range(self._special_len):
            found = PyUnicode_FindChar(val, self._special_char[i], start, end, 1)
            if found != -1:
                end = found
        return end

    cdef inline bint _is_literal_unsafe(self, Py_UCS4 ch) noexcept:
        cdef Py_ssize_t i
        for i in range(1, self._special_len):
            if ch == self._special_char[i]:
                return True
        return False
