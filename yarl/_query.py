"""Query string handling."""

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, SupportsInt, cast

from multidict import istr

from ._quoters import (
    QUERY_PART_QUOTER,
    QUERY_QUOTER,
    WHATWG_QUERY_PART_QUOTER,
    WHATWG_QUERY_QUOTER,
)
from ._quoting import _Quoter

SimpleQuery = str | SupportsInt | float
QueryVariable = SimpleQuery | Sequence[SimpleQuery]
Query = str | Mapping[str, QueryVariable] | Sequence[tuple[str, QueryVariable]] | None


def query_var(v: SimpleQuery) -> str:
    """Convert a query variable to a string.

    Note: Objects implementing the ``__int__`` data model method (typed as
    ``SupportsInt``; e.g. ``uuid.UUID``) are converted via ``int()`` first.
    Callers should convert such values to ``str`` explicitly if the string
    representation is desired.
    """
    cls = type(v)
    if cls is int:  # Fast path for non-subclassed int
        return str(v)
    if isinstance(v, str):
        return v
    if isinstance(v, float):
        if math.isinf(v):
            raise ValueError("float('inf') is not supported")
        if math.isnan(v):
            raise ValueError("float('nan') is not supported")
        return str(float(v))
    if cls is not bool and isinstance(v, SupportsInt):
        return str(int(v))
    raise TypeError(
        "Invalid variable type: value "
        "should be str, int or float, got {!r} "
        "of type {}".format(v, cls)
    )


def get_str_query_from_sequence_iterable(
    items: Iterable[tuple[str | istr, QueryVariable]],
    quoter: _Quoter = QUERY_PART_QUOTER,
) -> str:
    """Return a query string from a sequence of (key, value) pairs.

    value is a single value or a sequence of values for the key

    The sequence of values must be a list or tuple.
    """
    pairs = [
        f"{quoter(k)}={quoter(v if type(v) is str else query_var(v))}"
        for k, val in items
        for v in (
            val if type(val) is not str and isinstance(val, (list, tuple)) else (val,)
        )
    ]
    return "&".join(pairs)


def get_str_query_from_iterable(
    items: Iterable[tuple[str | istr, SimpleQuery]],
    quoter: _Quoter = QUERY_PART_QUOTER,
) -> str:
    """Return a query string from an iterable.

    The iterable must contain (key, value) pairs.

    The values are not allowed to be sequences, only single values are
    allowed. For sequences, use `_get_str_query_from_sequence_iterable`.
    """
    # A listcomp is used since listcomps are inlined on CPython 3.12+ and
    # they are a bit faster than a generator expression.
    pairs = [
        f"{quoter(k)}={quoter(v if type(v) is str else query_var(v))}" for k, v in items
    ]
    return "&".join(pairs)


def _make_get_str_query(
    query_quoter: _Quoter, part_quoter: _Quoter
) -> Callable[..., str | None]:
    """Make get_str_query() for a pair of quoters, see get_str_query_whatwg."""

    def get_str_query(*args: Any, **kwargs: Any) -> str | None:
        """Return a query string from supported args."""
        query: (
            str
            | Mapping[str, QueryVariable]
            | Sequence[tuple[str | istr, SimpleQuery]]
            | None
        )
        if kwargs:
            if args:
                msg = "Either kwargs or single query parameter must be present"
                raise ValueError(msg)
            query = kwargs
        elif len(args) == 1:
            query = args[0]
        else:
            raise ValueError("Either kwargs or single query parameter must be present")

        if query is None:
            return None
        if not query:
            return ""
        if type(query) is dict:
            return get_str_query_from_sequence_iterable(query.items(), part_quoter)
        if type(query) is str or isinstance(query, str):
            return query_quoter(query)
        if isinstance(query, Mapping):
            return get_str_query_from_sequence_iterable(query.items(), part_quoter)
        if isinstance(query, (bytes, bytearray, memoryview)):
            msg = "Invalid query type: bytes, bytearray and memoryview are forbidden"
            raise TypeError(msg)
        if isinstance(query, Sequence):
            # We don't expect sequence values if we're given a list of pairs
            # already; only mappings like builtin `dict` which can't have the
            # same key pointing to multiple values are allowed to use
            # `_query_seq_pairs`.
            if TYPE_CHECKING:
                query = cast(Sequence[tuple[str | istr, SimpleQuery]], query)
            return get_str_query_from_iterable(query, part_quoter)
        raise TypeError(
            "Invalid query type: only str, mapping or "
            "sequence of (key, value) pairs is allowed"
        )

    return get_str_query


get_str_query = _make_get_str_query(QUERY_QUOTER, QUERY_PART_QUOTER)
# WHATWG mode keeps "\\" in the query, see WHATWG_QUERY_QUOTER.
get_str_query_whatwg = _make_get_str_query(
    WHATWG_QUERY_QUOTER, WHATWG_QUERY_PART_QUOTER
)
