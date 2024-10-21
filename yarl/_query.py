import math
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, SupportsInt, Union

from multidict import istr  # Import for case-insensitive string handling

from ._quoters import QUERY_PART_QUOTER, QUERY_QUOTER  # Importing query quoters for URL encoding

# Define types for simple queries and query variables
SimpleQuery = Union[str, int, float]
QueryVariable = Union[SimpleQuery, Sequence[SimpleQuery]]
Query = Union[
    None, str, Mapping[str, QueryVariable], Sequence[tuple[str, QueryVariable]]
]

# Function to convert a query variable to a string
def query_var(v: QueryVariable) -> str:
    """Convert a query variable to a string."""
    cls = type(v)
    if cls is int:  # Fast path for non-subclassed int
        return str(v)  # Convert integer to string
    if issubclass(cls, str):  # If it's a string, return it as is
        if TYPE_CHECKING:
            assert isinstance(v, str)
        return v
    if cls is float or issubclass(cls, float):  # Handle floats
        if TYPE_CHECKING:
            assert isinstance(v, float)
        if math.isinf(v):  # Check for infinity values
            raise ValueError("float('inf') is not supported")
        if math.isnan(v):  # Check for NaN values
            raise ValueError("float('nan') is not supported")
        return str(float(v))  # Convert float to string
    if cls is not bool and isinstance(cls, SupportsInt):  # Handle other integer-like objects
        return str(int(v))
    raise TypeError(
        "Invalid variable type: value "
        "should be str, int or float, got {!r} "
        "of type {}".format(v, cls)
    )

# Function to generate a query string from a sequence of (key, value) pairs, where values can be sequences
def get_str_query_from_sequence_iterable(
    items: Iterable[tuple[Union[str, istr], QueryVariable]],
) -> str:
    """Return a query string from a sequence of (key, value) pairs.

    value is a single value or a sequence of values for the key

    The sequence of values must be a list or tuple.
    """
    quoter = QUERY_PART_QUOTER  # Function for URL-encoding parts of the query
    pairs = [
        f"{quoter(k)}={quoter(v if type(v) is str else query_var(v))}"
        for k, val in items  # Loop through key, value pairs
        for v in (
            val if type(val) is not str and isinstance(val, (list, tuple)) else (val,)
        )  # If the value is a sequence, iterate over it
    ]
    return "&".join(pairs)  # Join all key-value pairs with '&' to form the query string

# Function to generate a query string from an iterable of key-value pairs, but the values can't be sequences
def get_str_query_from_iterable(
    items: Iterable[tuple[Union[str, istr], SimpleQuery]]
) -> str:
    """Return a query string from an iterable.

    The iterable must contain (key, value) pairs.

    The values are not allowed to be sequences, only single values are
    allowed. For sequences, use `_get_str_query_from_sequence_iterable`.
    """
    quoter = QUERY_PART_QUOTER  # URL-encoding function for query parts
    pairs = [
        f"{quoter(k)}={quoter(v if type(v) is str else query_var(v))}" for k, v in items
    ]  # Format the key-value pairs
    return "&".join(pairs)  # Join key-value pairs with '&' to form the query string

# Function to handle different ways of passing query parameters and return a query string
def get_str_query(*args: Any, **kwargs: Any) -> Union[str, None]:
    """Return a query string from supported args."""
    query: Union[str, Mapping[str, QueryVariable], None]
    
    # If kwargs are provided, ensure no args are provided at the same time
    if kwargs:
        if args:
            msg = "Either kwargs or single query parameter must be present"
            raise ValueError(msg)
        query = kwargs  # Use kwargs as the query
    elif len(args) == 1:  # If only one argument is provided, use it as the query
        query = args[0]
    else:
        raise ValueError("Either kwargs or single query parameter must be present")

    # Handle empty or None query cases
    if query is None:
        return None  # Return None if query is None
    if not query:
        return ""  # Return an empty string for empty query
    
    # Convert different types of queries to strings
    if isinstance(query, Mapping):  # If query is a mapping (e.g., dict), handle it as key-value pairs
        return get_str_query_from_sequence_iterable(query.items())
    if isinstance(query, str):  # If query is a string, URL-encode it
        return QUERY_QUOTER(query)
    if isinstance(query, (bytes, bytearray, memoryview)):  # Raise error for unsupported types
        msg = "Invalid query type: bytes, bytearray and memoryview are forbidden"
        raise TypeError(msg)
    if isinstance(query, Sequence):  # If query is a sequence of pairs, handle it as key-value pairs
        return get_str_query_from_iterable(query)
    
    # Raise error for unsupported types
    raise TypeError(
        "Invalid query type: only str, mapping or "
        "sequence of (key, value) pairs is allowed"
    )
