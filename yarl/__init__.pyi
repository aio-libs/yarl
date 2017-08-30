from typing import overload, Tuple, Optional, Mapping, Union, Sequence
import multidict


class URL:
    scheme = ...  # type: str
    raw_user = ...  # type: str
    user = ...  # type: Optional[str]
    raw_password = ...  # type: Optional[str]
    password = ...  # type: Optional[str]
    raw_host = ...  # type: Optional[str]
    host = ...  # type: Optional[str]
    port = ...  # type: Optional[int]
    raw_path = ...  # type: str
    path = ...  # type: str
    raw_query_string = ...  # type: str
    query_string = ...  # type: str
    raw_fragment = ...  # type: str
    fragment = ...  # type: str
    query = ...  # type: multidict.MultiDict
    raw_name = ...  # type: str
    name = ...  # type: str
    raw_parts = ...  # type: Tuple[str, ...]
    parts = ...  # type: Tuple[str, ...]
    parent = ...  # type: URL

    def __init__(self, val: Union[str, 'URL'], *, encoded: bool=...,
                strict: bool=...) -> None: ...

    @classmethod
    def build(cls, *, scheme: str=..., user: str=..., password: str=...,
              host: str=..., port: int=..., path: str=...,
              query: Mapping=..., query_string: str=...,
              fragment: str=..., strict: bool=...) -> URL: ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

    def __eq__(self, other) -> bool: ...
    def __le__(self, other) -> bool: ...
    def __lt__(self, other) -> bool: ...
    def __ge__(self, other) -> bool: ...
    def __gt__(self, other) -> bool: ...
    def __hash__(self) -> int: ...

    def __truediv__(self, str) -> URL: ...

    def is_absolute(self) -> bool: ...
    def is_default_port(self) -> bool: ...

    def origin(self) -> URL: ...
    def relative(self) -> URL: ...

    def with_scheme(self, scheme: str) -> URL: ...
    def with_user(self, user: Optional[str]) -> URL: ...
    def with_password(self, password: Optional[str]) -> URL: ...
    def with_host(self, host: str) -> URL: ...
    def with_port(self, port: Optional[int]) -> URL: ...
    def with_path(self, path: str) -> URL: ...

    @overload
    def with_query(self, query: str) -> URL: ...
    @overload
    def with_query(self, query: Mapping[str, str]) -> URL: ...
    @overload
    def with_query(self, query: Sequence[Tuple[str, str]]) -> URL: ...
    @overload
    def with_query(self, **kwargs) -> URL: ...

    @overload
    def update_query(self, query: str) -> URL: ...
    @overload
    def update_query(self, query: Mapping[str, str]) -> URL: ...
    @overload
    def update_query(self, query: Sequence[Tuple[str, str]]) -> URL: ...
    @overload
    def update_query(self, **kwargs) -> URL: ...

    def with_fragment(self, fragment: Optional[str]) -> URL: ...
    def with_name(self, name: str) -> URL: ...

    def join(self, url: URL) -> URL: ...

    def human_repr(self) -> str: ...
