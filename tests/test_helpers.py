import platform

import pytest

from yarl import _helpers

IS_PYPY = platform.python_implementation() == "PyPy"


class CachedPropertyMixin:
    cached_property = NotImplemented

    def test_cached_property(self) -> None:
        class A:
            def __init__(self):
                self._cache = {}

            @self.cached_property  # type: ignore[misc]
            def prop(self):
                return 1

        a = A()
        assert 1 == a.prop

    def test_cached_property_class(self) -> None:
        class A:
            def __init__(self):
                self._cache = {}

            @self.cached_property  # type: ignore[misc]
            def prop(self):
                """Docstring."""
                return 1

        assert isinstance(A.prop, self.cached_property)
        assert "Docstring." == A.prop.__doc__

    def test_cached_property_assignment(self) -> None:
        class A:
            def __init__(self):
                self._cache = {}

            @self.cached_property  # type: ignore[misc]
            def prop(self):
                return 1

        a = A()

        with pytest.raises(AttributeError):
            a.prop = 123

    def test_cached_property_without_cache(self) -> None:
        class A:
            def __init__(self):
                pass

            @self.cached_property  # type: ignore[misc]
            def prop(self):
                return 1

        a = A()

        with pytest.raises(AttributeError):
            a.prop = 123

    def test_cached_property_check_without_cache(self) -> None:
        class A:
            def __init__(self):
                pass

            @self.cached_property  # type: ignore[misc]
            def prop(self):
                return 1

        a = A()
        with pytest.raises(AttributeError):
            assert 1 == a.prop


class TestPyCachedProperty(CachedPropertyMixin):
    cached_property = _helpers.cached_property_py  # type: ignore[assignment]


if (
    not _helpers.NO_EXTENSIONS
    and not IS_PYPY
    and hasattr(_helpers, "cached_property_c")
):

    class TestCCachedProperty(CachedPropertyMixin):
        cached_property = _helpers.cached_property_c  # type: ignore[attr-defined, unused-ignore] # noqa: E501
