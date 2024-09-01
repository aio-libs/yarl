from typing import Any

class cached_property:
    def __init__(self, wrapped: Any) -> None: ...  # pragma: no cover
    def __get__(self, inst: Any, owner: Any) -> Any: ...  # pragma: no cover
    def __set__(self, inst: Any, value: Any) -> None: ...  # pragma: no cover
