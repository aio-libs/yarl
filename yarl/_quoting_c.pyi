from typing import Optional

class _Quoter:
    def __init__(
        self,
        *,
        safe: str = ...,
        protected: str = ...,
        qs: bool = ...,
        requote: bool = ...
    ) -> None: ...
    def __call__(self, val: str = ...) -> str: ...

class _Unquoter:
    def __init__(self, *, unsafe: str = ..., qs: bool = ...) -> None: ...
    def __call__(self, val: str = ...) -> str: ...
